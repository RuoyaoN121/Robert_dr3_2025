import numpy as np
import pickle
import json
import glob
import os
import sys
import debugpy

import matplotlib.pyplot as plt

import enterprise
from enterprise.pulsar import Pulsar
import enterprise.signals.parameter as eparameter
from enterprise.signals import utils
from enterprise.signals import signal_base
from enterprise.signals import selections
from enterprise.signals.selections import Selection
from enterprise.signals import white_signals
from enterprise.signals import gp_signals
from enterprise.signals import deterministic_signals
from enterprise.signals import gp_bases
import enterprise.constants as const
from enterprise_extensions.chromatic.solar_wind import solar_wind, createfourierdesignmatrix_solar_dm
import enterprise_extensions
from enterprise_extensions import models, model_utils, hypermodel, blocks
from enterprise_extensions import timing
from enterprise_extensions.frequentist import optimal_statistic as opt_stat
import time
import h5py
import dill

Optstat_dir = r'/fred/oz002/users/mbailes/astral/timing2025/Optstat'

def weightedavg(rho,sig):
    weights, avg=0.,0.
    for r,s in zip(rho,sig):
        weights += 1./(s*s)
        avg += r/(s*s)

    return avg/weights, np.sqrt(1./weights)

def bin_crosscor(zeta,zi,rho,sig):

    rho_avg,sig_avg=np.zeros(len(zeta)), np.zeros(len(zeta))

    for i,z in enumerate(zeta[:-1]):
        myrhos, mysigs = [], []
        for x,r,s in zip(xi,rho,sig):
            if x>=z and x < (z+10):
                myrhos.append(r)
                myrhos.append(s)
        rho_avg[i],sig_avg[i]=weightedavg(myrhos,mysigs)
    return rho_avg, sig_avg

def get_HD_curve(zeta):
    coszeta=np.cos(zeta*np.pi/180.)
    xip=(1.-coszeta)/2.
    HD=3.*(1./3.+xip*(np.log(xip) -1./6.))

    return HD/2.



no_selection=selections.Selection(selections.no_selection)
by_backend = selections.Selection(selections.by_backend)

def low_frequencies(freqs):
    """Selection for obs frequencies <=960MHz"""
    return dict(zip(['low'], [freqs <= 1284]))

def high_frequencies(freqs):
    """Selection for obs frequencies >=2048MHz"""
    return dict(zip(['high'], [freqs > 1284]))

low_freq = selections.Selection(low_frequencies)
high_freq = selections.Selection(high_frequencies)


datadir = str(sys.argv[1])
print(sys.argv[1])
#datadir = "/fred/oz002/users/mbailes/astral/timing2025/GWB_search_1/"

parfiles=sorted(glob.glob(datadir+'J*.par'))
#parfiles=sorted(glob.glob(pardir+'J*.par'))

timfiles=sorted(glob.glob(datadir+'J*.tim'))
#timfiles=sorted(glob.glob(timdir+'J*.tim'))

psrs = []
ephemeris =  'DE440'

for p, t in zip(parfiles,timfiles):

    print(p)
    psr=Pulsar(p,t,ephem=ephemeris)

    psrs.append(psr)

noisefile = '/fred/oz002/users/mmiles/for_matthew/OptStat/noisefiles/MPTA_WN_values.json'

with open(noisefile, 'r') as f:
    noisedict=json.load(f)

def dm_noise(log10_A,gamma,Tspan,components=30,option="powerlaw"):
    """
    A term to account for stochastic variations in DM. It is based on spin
    noise model, with Fourier amplitudes depending on radio frequency nu
    as ~ 1/nu^2.
    """
    nfreqs = 30
    if option=="powerlaw":
      #pl = utils.powerlaw(log10_A=log10_A, gamma=gamma, components=components)
      pl = utils.powerlaw(log10_A=log10_A, gamma=gamma)
      #pl = enterprise.signals.gp_priors.powerlaw_no_components(log10_A=log10_A, gamma=gamma)

    #elif option=="turnover":
    #  fc = parameter.Uniform(self.params.sn_fc[0],self.params.sn_fc[1])
    #  pl = powerlaw_bpl(log10_A=log10_A, gamma=gamma, fc=fc,
    #                    components=components)
    dm_basis = utils.createfourierdesignmatrix_dm(nmodes = components,
                                                  Tspan=Tspan)
    dmn = gp_signals.BasisGP(pl, dm_basis, name='dm_gp')

    return dmn

@signal_base.function
def chrom_yearly_sinusoid(toas, freqs, log10_Amp, phase, idx):
    """
    Chromatic annual sinusoid.
    :param log10_Amp: amplitude of sinusoid
    :param phase: initial phase of sinusoid
    :param idx: index of chromatic dependence
    :return wf: delay time-series [s]
    """

    wf = 10**log10_Amp * np.sin(2 * np.pi * const.fyr * toas + phase)
    return wf * (1400 / freqs) ** idx


@signal_base.function
def chrom_gaussian_bump(toas, freqs, log10_Amp=-2.5, sign_param=1.0,
                    t0=53890, sigma=81, idx=2):
    """
    Chromatic time-domain Gaussian delay term in TOAs.
    Example: J1603-7202 in Lentati et al, MNRAS 458, 2016.
    """
    #t0 *= const.day
    #sigma *= const.day
    wf = 10**log10_Amp * np.exp(-(toas - t0)**2/2/sigma**2)
    return np.sign(sign_param) * wf * (1400 / freqs) ** idx

def dm_gaussian_bump(tmin, tmax, idx=2, sigma_min=600000, sigma_max=1000,
    log10_A_low=-10, log10_A_high=-1, name='dm_bump'):
    """
    Returns chromatic Gaussian bump (i.e. TOA advance):
    :param tmin, tmax:
        search window for exponential cusp time.
    :param idx:
        index of radio frequency dependence (i.e. DM is 2). If this is set
        to 'vary' then the index will vary from 1 - 6
    :param sigma_min, sigma_max:
        standard deviation of a Gaussian in MJD
    :param sign:
        [boolean] allow for positive or negative exponential features.
    :param name: Name of signal
    :return dm_bump:
        chromatic Gaussian bump waveform.
    """
    sign_param = eparameter.Uniform(-1,1)
    t0_dm_bump = eparameter.Uniform(tmin,tmax)
    sigma_dm_bump = eparameter.Uniform(sigma_min,tmax-tmin)
    log10_Amp_dm_bump = eparameter.Uniform(log10_A_low, log10_A_high)
    if idx == 'vary':
        idx = eparameter.Uniform(0, 14)
    wf = chrom_gaussian_bump(log10_Amp=log10_Amp_dm_bump,
                         t0=t0_dm_bump, sigma=sigma_dm_bump,
                         sign_param=sign_param, idx=idx)
    dm_bump = deterministic_signals.Deterministic(wf, name=name)

    return dm_bump

gamma_gw=4.33

Tspanall=model_utils.get_tspan(psrs)

efac = eparameter.Constant()
equad = eparameter.Constant()
ecorr = eparameter.Constant()

def mk_band_split(freqs, backend_flags):
    """ Selection for splitting the band in 3 """
    d =  dict(zip(['low', 'high', 'all'],
                  [(freqs <= 1100), (freqs > 1100), (freqs >= 0)]))
    delkeys = []
    for key in d.keys():
        if np.sum(d[key]) == 0:  # all False
            delkeys.append(key)
    for key in delkeys:
        del d[key]
    return d

mk_ecorr_selection = selections.Selection(mk_band_split)


models = []



crn = blocks.common_red_noise_block(psd='powerlaw', prior='log-uniform', Tspan=Tspanall, components=3,gamma_val=gamma_gw, name='gw')


for pulsar in psrs:

    s = gp_signals.TimingModel(use_svd=True)

    if pulsar.name+"_KAT_MKBF_log10_tnequad" in noisedict.keys():
        eq = white_signals.TNEquadNoise(log10_tnequad=equad, selection=by_backend)
        s += eq
    
    ef = white_signals.MeasurementNoise(efac=efac, selection=by_backend)
    s += ef
    
    if pulsar.name+"_basis_ecorr_KAT_MKBF_log10_ecorr" in noisedict.keys():
        #ec = white_signals.EcorrKernelNoise(log10_ecorr=ecorr, selection=by_backend)
        ec = gp_signals.EcorrBasisModel(log10_ecorr=ecorr,selection=by_backend)
        s += ec

    if pulsar.name+"_basis_ecorr_all_log10_ecorr" in noisedict.keys():
        ec = gp_signals.EcorrBasisModel(log10_ecorr=ecorr,selection=mk_ecorr_selection)
        s += ec

    tmin = pulsar.toas.min()
    tmax = pulsar.toas.max()
    Tspan=(tmax-tmin)

    max_cadence = 60  # days
    components = 120
    freqs = np.linspace(1/Tspan,30/Tspan,30)

    ev_json = json.load(open('/fred/oz002/users/mmiles/for_matthew/OptStat/noisefiles/MPTA_noise_models.json'))

    keys = list(ev_json.keys())
    # Get list of models
    psrmodels = [ psr_model for psr_model in keys if pulsar.name in psr_model ][0].split("_")[1:]



    # if pulsar.name+"_red_noise_log10_A" in noisedict.keys():
    #     log10_A_red = eparameter.Uniform(-20, -11)
    #     gamma_red = eparameter.Uniform(0, 7)
    #     pl = utils.powerlaw(log10_A=log10_A_red, gamma=gamma_red)
    #     rn = gp_signals.FourierBasisGP(spectrum=pl, components=120, Tspan=Tspan)
    #     s += rn

    high_comps = 120
    for i, pm in enumerate(psrmodels):
        if pm =="DM":
            if ( i+1 < len(psrmodels) and psrmodels[i+1] != "WIDE" ):
                log10_A_dm = eparameter.Uniform(-20, -11)
                gamma_dm = eparameter.Uniform(0, 7)
                dm = dm_noise(log10_A=log10_A_dm,gamma=gamma_dm,Tspan=Tspan,components=high_comps,option="powerlaw")
                s += dm
            elif i+1 == len(psrmodels):
                log10_A_dm = eparameter.Uniform(-20, -11)
                gamma_dm = eparameter.Uniform(0, 7)
                dm = dm_noise(log10_A=log10_A_dm,gamma=gamma_dm,Tspan=Tspan,components=high_comps,option="powerlaw")
                s += dm 
        
        if pm == "DMWIDE" or ( pm == "DM" and ( i+1 < len(psrmodels) and psrmodels[i+1] == "WIDE" ) ):
            log10_A_dm = eparameter.Uniform(-20, -11)
            gamma_dm = eparameter.Uniform(0, 14)
            dm = dm_noise(log10_A=log10_A_dm,gamma=gamma_dm,Tspan=Tspan,components=120,option="powerlaw")
            s += dm

        if pm == "RN":
        
            log10_A_red = eparameter.Uniform(-20, -11)
            gamma_red = eparameter.Uniform(0, 7)
            pl = utils.powerlaw(log10_A=log10_A_red, gamma=gamma_red)
            rn = gp_signals.FourierBasisGP(spectrum=pl, components=120, Tspan=Tspan)
            s += rn

        if pm == "CHROM":
            if ( i+1 < len(psrmodels) and psrmodels[i+1] != "WIDE" ):
                log10_A_chrom_prior = eparameter.Uniform(-20, -11)
                gamma_chrom_prior = eparameter.Uniform(0, 14)
                chrom_gp_idx = eparameter.Uniform(0,14)
                chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
                idx = chrom_gp_idx
                components = high_comps
                chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                        idx=idx)
                chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom_gp')
                s += chrom
            elif i+1 == len(psrmodels):
                log10_A_chrom_prior = eparameter.Uniform(-20, -11)
                gamma_chrom_prior = eparameter.Uniform(0, 14)
                chrom_gp_idx = eparameter.Uniform(0,14)
                chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
                idx = chrom_gp_idx
                components = high_comps
                chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                        idx=idx)
                chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom_gp')
                s += chrom

        if pm == "CHROM2":
            if ( i+1 < len(psrmodels) and psrmodels[i+1] != "WIDE" ):
                log10_A_chrom_prior = eparameter.Uniform(-20, -11)
                gamma_chrom_prior = eparameter.Uniform(0, 14)
                chrom_gp_idx = eparameter.Uniform(0,14)
                chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
                idx = chrom_gp_idx
                components = high_comps
                chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                        idx=idx)
                chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom2_gp')
                s += chrom
            elif i+1 == len(psrmodels):
                log10_A_chrom_prior = eparameter.Uniform(-20, -11)
                gamma_chrom_prior = eparameter.Uniform(0, 14)
                chrom_gp_idx = eparameter.Uniform(0,14)
                chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
                idx = chrom_gp_idx
                components = high_comps
                chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                        idx=idx)
                chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom2_gp')
                s += chrom

        if pm == "CHROMWIDE" or ( pm == "CHROM" and ( i+1 < len(psrmodels) and psrmodels[i+1] == "WIDE" ) ):
            log10_A_chrom_prior = eparameter.Uniform(-20, -11)
            gamma_chrom_prior = eparameter.Uniform(0, 14)
            chrom_gp_idx = eparameter.Uniform(0,14)
            chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
            idx = chrom_gp_idx
            components = 120
            chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                    idx=idx)
            chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom_gp')
            s += chrom

        if pm == "CHROMCIDX":
            if ( i+1 < len(psrmodels) and psrmodels[i+1] != "WIDE" ):
                log10_A_chrom_prior = eparameter.Uniform(-20, -11)
                gamma_chrom_prior = eparameter.Uniform(0, 7)
                chrom_gp_idx = eparameter.Constant(4)
                chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
                idx = chrom_gp_idx
                components = high_comps
                chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                        idx=idx)
                chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom_gp')
                s += chrom
            elif i+1 == len(psrmodels):
                log10_A_chrom_prior = eparameter.Uniform(-20, -11)
                gamma_chrom_prior = eparameter.Uniform(0, 7)
                chrom_gp_idx = eparameter.Constant(4)
                chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
                idx = chrom_gp_idx
                components = high_comps
                chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                        idx=idx)
                chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom_gp')
                s += chrom

        if pm == "CHROMCIDXWIDE" or ( pm == "CHROMCIDX" and ( i+1 < len(psrmodels) and psrmodels[i+1] == "WIDE" ) ):
            log10_A_chrom_prior = eparameter.Uniform(-20, -11)
            gamma_chrom_prior = eparameter.Uniform(0, 14)
            chrom_gp_idx = eparameter.Constant(4)
            chrom_model = utils.powerlaw(log10_A=log10_A_chrom_prior, gamma=gamma_chrom_prior)
            idx = chrom_gp_idx
            components = 120
            chrom_basis = gp_bases.createfourierdesignmatrix_chromatic(nmodes=components,
                                                                    idx=idx)
            chrom = gp_signals.BasisGP(chrom_model, chrom_basis, name='chrom_gp')
            s += chrom

        if pm == "CHROMANNUAL":
            log10_Amp_chrom1yr = eparameter.Uniform(-20, -5)
            phase_chrom1yr = eparameter.Uniform(0, 2*np.pi)
            idx_chrom1yr = eparameter.Uniform(0, 14)
            wf = chrom_yearly_sinusoid(log10_Amp=log10_Amp_chrom1yr, phase=phase_chrom1yr, idx=idx_chrom1yr)
            chrom1yr = deterministic_signals.Deterministic(wf, name="chrom1yr")
            s += chrom1yr

        if pm == "SW":
            n_earth = eparameter.Uniform(0, 20)
            deter_sw = solar_wind(n_earth=n_earth)
            mean_sw = deterministic_signals.Deterministic(deter_sw, name='n_earth')

            Tspan = psr.toas.max() - psr.toas.min()
            max_cadence = 60
            sw_components = 120

            log10_A_sw = eparameter.Uniform(-10, 1)
            gamma_sw = eparameter.Uniform(-4, 4)
            sw_prior = utils.powerlaw(log10_A=log10_A_sw, gamma=gamma_sw)
            sw_basis = createfourierdesignmatrix_solar_dm(nmodes=sw_components, Tspan=Tspan)

            sw = mean_sw + gp_signals.BasisGP(sw_prior, sw_basis, name='gp_sw')

            s += sw
        
        if pm == "SWDET":
            n_earth = eparameter.Uniform(0, 20)
            deter_sw = solar_wind(n_earth=n_earth)
            mean_sw = deterministic_signals.Deterministic(deter_sw, name='n_earth')

            sw = mean_sw

            s += sw

        if pm == "CHROMBUMP":
            chrom_gauss_bump = dm_gaussian_bump(tmin, tmax, idx="vary", sigma_min=604800, sigma_max=tmax-tmin, log10_A_low=-10, log10_A_high=-1, name='chrom_bump')
            s += chrom_gauss_bump
        
    if "SW" not in psrmodels and "SWDET" not in psrmodels:
        n_earth = eparameter.Constant(4)
        deter_sw = solar_wind(n_earth=n_earth)
        mean_sw = deterministic_signals.Deterministic(deter_sw, name='n_earth')

        sw = mean_sw

        s += sw

    # log10_A_red = eparameter.Uniform(-20, -11)
    # gamma_red = eparameter.Uniform(0, 7)
    # pl = utils.powerlaw(log10_A=log10_A_red, gamma=gamma_red)
    # rn = gp_signals.FourierBasisGP(spectrum=pl, components=120, Tspan=Tspan)
    # s += rn

    s += crn

    models.append(s(pulsar))


pta = signal_base.PTA(models)

pta.set_default_params(noisedict)

#pta = dill.load(open("/fred/oz002/users/mmiles/MPTA_GW/enterprise_ozstar2/out_ptmcmc/pta_objects/PTA_CRN_ER.pkl","rb"))

ostat = opt_stat.OptimalStatistic(psrs, gamma_common=gamma_gw, pta=pta, orf='hd', bayesephem=False)
ostat_dip = opt_stat.OptimalStatistic(psrs, gamma_common=gamma_gw, pta=pta, orf='dipole',bayesephem=False)
ostat_mono = opt_stat.OptimalStatistic(psrs, gamma_common=gamma_gw, pta=pta, orf='monopole',bayesephem=False)


with open('/fred/oz002/users/mmiles/for_matthew/OptStat/noisefiles/MPTA_red_noise_values.json', "r") as f:
    ml_params = json.load(f)


dirname = datadir.split('/')[1]
outdir = os.path.join(Optstat_dir, dirname)
os.makedirs(outdir, exist_ok=True)

xi, rho, sig, OS, OS_sig = ostat.compute_os(params=ml_params)
print(OS, OS_sig, OS/OS_sig)

_, _, _, OS_dip, OS_sig_dip = ostat_dip.compute_os(params=ml_params)
print(OS_dip, OS_sig_dip, OS_dip/OS_sig_dip)

_, _, _, OS_mono, OS_sig_mono = ostat_mono.compute_os(params=ml_params)
print(OS_mono, OS_sig_mono, OS_mono/OS_sig_mono)

print('multiple correlations')

xi, rho, sig, multi_corr_OS, multi_corr_OS_sig = ostat.compute_multiple_corr_os(params=ml_params)
print(multi_corr_OS, multi_corr_OS_sig, multi_corr_OS/multi_corr_OS_sig)

_, _, _, multi_corr_OS_dip, multi_corr_OS_sig_dip = ostat_dip.compute_multiple_corr_os(params=ml_params)
print(multi_corr_OS_dip, multi_corr_OS_sig_dip, multi_corr_OS_dip/multi_corr_OS_sig_dip)

_, _, _, multi_corr_OS_mono, multi_corr_OS_sig_mono = ostat_mono.compute_multiple_corr_os(params=ml_params)
print(multi_corr_OS_mono, multi_corr_OS_sig_mono, multi_corr_OS_mono/multi_corr_OS_sig_mono)

with open(os.path.join(outdir, 'SNR.dat'), "w+") as f:
    f.write(f"{OS} {OS_sig} {OS/OS_sig}\n {OS_dip} {OS_sig_dip} {OS_dip/OS_sig_dip}\n {OS_mono} {OS_sig_mono} {OS_mono/OS_sig_mono}\n")
    f.write('multiple correlations\n')
    f.write(f"{multi_corr_OS} {multi_corr_OS_sig} {multi_corr_OS/multi_corr_OS_sig}\n {multi_corr_OS_dip} {multi_corr_OS_sig_dip} {multi_corr_OS_dip/multi_corr_OS_sig_dip}\n {multi_corr_OS_mono} {multi_corr_OS_sig_mono} {multi_corr_OS_mono/multi_corr_OS_sig_mono}")
f.close()


idx=np.argsort(xi)

xi_sorted = xi[idx]
rho_sorted = rho[idx]
sig_sorted = sig[idx]


npsr=np.shape(psrs)[0]

gof=np.zeros(npsr)
rho2=np.zeros(npsr)
sig2=np.zeros(npsr)

rho_expected=6.3682499e-29*get_HD_curve(xi)



f = open(os.path.join(outdir, 'crosscorr.dat'), "w+")

i=0
for ii in range(npsr-1):
    for jj in range(ii+1,npsr):
        #print(i, ii,jj)
        gof[ii] += ((rho[i]-rho_expected[i])/sig[i])**2
        gof[jj] += ((rho[i]-rho_expected[i])/sig[i])**2
        rho2[ii] += (rho[i]-rho_expected[i])**2
        rho2[jj] += (rho[i]-rho_expected[i])**2
        sig2[ii] += sig[i]**2
        sig2[jj] += sig[i]**2
        f.write("{0} {1} {2} {3} {4} {5} \n".format(psrs[ii].name,psrs[jj].name, rho[i]/sig[i],rho[i],sig[i],xi[i]))
        i=i+1

f.close()

for i in range(npsr):
    print(psrs[i].name, gof[i], rho2[i],sig2[i])





npairs = 120
#npairs = 230

xi_mean = []
xi_err = []
rho_avg = []
sig_avg = []

i=0

while i < len(xi_sorted):
    xi_mean.append(np.mean(xi_sorted[i:npairs+i]))
    xi_err.append(np.std(xi_sorted[i:npairs+i]))

    r,s=weightedavg(rho_sorted[i:npairs+i],sig_sorted[i:npairs+i])
    rho_avg.append(r)
    sig_avg.append(s)

    i+= npairs

xi_mean=np.array(xi_mean)
xi_err=np.array(xi_err)

fig,ax = plt.subplots(figsize=(12,7))
#plt.figure(figsize=(10,7))
(_, caps, _) = ax.errorbar(xi_mean*180/np.pi, rho_avg, xerr=xi_err*180/np.pi, yerr=sig_avg, marker='o', ls='', 
                                    color='#003f5c', fmt='o', capsize=7.5, elinewidth=3.2, label = "MPTA interpulsar correlations", zorder=10)
zeta=np.linspace(0.01,180,100)

HD=get_HD_curve(zeta)
#plt.title("OS: {0:.2E}; SNR: {1:.2f}".format(OS, OS/OS_sig))
ax.plot(zeta, OS*HD, ls='--', label='Hellings-Downs', color='#117733', lw=3, zorder=1)
#plt.plot(zeta, zeta*0.0+OS_mono, ls='--', label='Monopole', color='C1', lw=1.5)
#plt.plot(zeta, OS_dip*np.cos(zeta*np.pi/180), ls='--', label='Dipole', color='C2', lw=1.5)

ax.set_xlim(0, 180)
#plt.ylim(-1e-29, 1e-29)
ax.set_ylabel(r'$\hat{A}^2 \Gamma(\zeta_{ab})$', fontsize=15)
ax.set_xlabel(r'$\zeta$ ($^{\circ}$)', fontsize=15)
ax.legend(loc=1, fontsize=15)
#plt.tick_params(labelsize=12, which="both")
ax.tick_params(labelsize=15, which="both")
ax.yaxis.offsetText.set_fontsize(15)
#plt.show()
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'Hellings_and_Downs.png'), dpi=100)
plt.clf()
fig.clf()
