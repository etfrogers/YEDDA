#!/usr/bin/env bash

tag=$1
if echo ${tag} | grep -qe '^v[0-9]\+\.[0-9]\+\.[0-9]\+$'
then
    echo "Format OK"
else
    echo "Version number does not match required format: v0.0.0"
    exit 1
fi
prettyVer=${tag/v/"Version "}
echo ${prettyVer} > version.txt
echo ${tag} >> version.txt
echo "Setting version to:"
cat version.txt
git add version.txt
git commit --amend --no-edit
git tag -a ${tag}
curr_branch=`git rev-parse --abbrev-ref HEAD`
git checkout release && git merge ${curr_branch} --ff-only && git checkout ${curr_branch}
build.sh ${tag}