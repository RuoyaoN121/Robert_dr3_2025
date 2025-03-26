cd ../partim_obs

for dir in J17* J18* J19* J20* J21* J22* J23*; do
    if [ -d "$dir" ]; then
        tmp_dir=$(mktemp -d)  # Create a unique temporary directory
        mv "$dir" "$tmp_dir/"
        echo "Moved $dir to $tmp_dir"
    fi
done