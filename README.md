# persuasion_parlai_data_collection

In its current state, launching mturk tasks with this repo will only work with Mac OSX. This is due to the fact that it contains a certain standalone version of the heroku cli which is only 
compatible with Mac OSX. To use this repo on a different OS you can run the following commands:

wget https://cli-assets.heroku.com/heroku-cli/channels/stable/heroku-cli-REPLACEME_OS-REPLACE_ME_ARCH.tar.gz -O heroku.tar.gz

tar -xvzf heroku.tar.gz

Where REPLACE_ME_OS is one of “linux”, “darwin”, “windows” and REPLACE_ME_ARCH is one of “x64” or “x86”

This will download another standalone heroku cli that is compatible with your OS. 
You can then replace the "node" and "heroku" files in parlai_old/parlai/mturk/core/heroku-cli-v6.99.0-ec9edad-darwin-x64/bin with the "node" and "heroku" files in the directory you just downloaded.
