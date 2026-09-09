#!/bin/bash

calculate_md5() {
    local file_path="$1"
    if command -v md5sum >/dev/null 2>&1; then
        md5sum "$file_path" | cut -d' ' -f1
    elif command -v md5 >/dev/null 2>&1; then
        md5 -q "$file_path"
    else
        echo "Error: No MD5 command available" >&2
        exit 1
    fi
}
 
# Copy asset files into a flat destination directory with firmware resource names.
copy_and_rename_assets() {
    local src_dir="$1"
    local dest_dir="$2"
    
    mkdir -p "$dest_dir"
    
    local temp_src_list=$(mktemp)
    local temp_dest_list=$(mktemp)
    
    find "$src_dir" -type f | while read -r src_file; do
        rel_path="${src_file#$src_dir/}"

        if [[ "$(basename "$rel_path")" == ".gitattributes" ]]; then
            continue
        fi
        
        IFS='/' read -ra path_parts <<< "$rel_path"
        first_dir="${path_parts[0]}"
        
        if [[ "$first_dir" == "default" ]]; then
            if [[ ${#path_parts[@]} -gt 1 ]]; then
                unset path_parts[0]
                new_filename=$(IFS='_'; echo "${path_parts[*]}")
            else
                new_filename="${path_parts[0]}"
            fi
        else
            if [[ ${#first_dir} -ge 2 ]]; then
                first_dir_prefix="${first_dir:0:2}"
            else
                first_dir_prefix="$first_dir"
            fi
            
            if [[ ${#path_parts[@]} -gt 1 ]]; then
                unset path_parts[0]
                remaining=$(IFS='_'; echo "${path_parts[*]}")
                new_filename="${first_dir_prefix}_${remaining}"
            else
                new_filename="$first_dir_prefix"
            fi
        fi
        
        dest_file="$dest_dir/$new_filename"
        
        src_md5=$(calculate_md5 "$src_file")
        
        echo "$new_filename|$src_file|$src_md5|$dest_file" >> "$temp_src_list"
    done
    
    wait
    
    if [[ -d "$dest_dir" ]]; then
        find "$dest_dir" -type f -exec basename {} \; > "$temp_dest_list"
    fi
    
    while IFS='|' read -r new_filename src_path src_md5 dest_file; do
        if [[ -f "$dest_file" ]]; then
            dest_md5=$(calculate_md5 "$dest_file")
            if [[ "$src_md5" == "$dest_md5" ]]; then
                echo "Skipped unchanged: $src_path -> $dest_file"
            else
                cp -p "$src_path" "$dest_file"
                echo "Copied: $src_path -> $dest_file"
            fi
        else
            cp -p "$src_path" "$dest_file"
            echo "Copied: $src_path -> $dest_file"
        fi
    done < "$temp_src_list"
    
    local temp_keep_list=$(mktemp)
    while IFS='|' read -r new_filename src_path src_md5 dest_file; do
        echo "$new_filename" >> "$temp_keep_list"
    done < "$temp_src_list"
    
    while IFS= read -r dest_file; do
        if ! grep -Fxq "$dest_file" "$temp_keep_list"; then
            rm "$dest_dir/$dest_file"
            echo "Removed stale file: $dest_dir/$dest_file"
        fi
    done < "$temp_dest_list"
    
    rm "$temp_src_list" "$temp_dest_list" "$temp_keep_list"
}
 
# Validate command-line arguments.
if [ $# -ne 2 ]; then
    echo "Usage: $0 <source_dir> <destination_dir>"
    echo "Example: $0 core/src/trezor/lvglui/assets dist-res"
    exit 1
fi
 
src_directory="$1"
dest_directory="$2"
 
copy_and_rename_assets "$src_directory" "$dest_directory"
echo "Asset sync completed."
