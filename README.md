# AWSer
A nifty little CLI tool to SSH to EC2 instances using their names

## Background
Have you ever done this?
1. Login to EC2 Console.
2. Search for an instance.
3. Copy its IP address.
4. Switch to a terminal.
5. Type `ssh` and paste in the IP.
6. Repeat 2-5 for other instances.

I've been in that situation more times than I care to admit. Enter AWSer: A simple Python script that will make your life 95% easier... at least when it comes to SSH'ing into EC2s!

## Demo
[![asciicast](https://asciinema.org/a/W9lHWY02nFwfkzSiYOy6RHXH5.svg)](https://asciinema.org/a/W9lHWY02nFwfkzSiYOy6RHXH5)

## Installation
1. Download the `awser.py` script and place it in a folder in your path.
2. [optional] Create a short symlink or alias such as `a` that points to the script.
3. Install boto3 if you don't already have it installed: `pip3 install boto3 --user`
4. Make sure you've configured your AWS credentials via `aws configure`.
5. Start using AWSer!

## Usage
```
usage: awser.py [-h] [-r REGION] [-u USER] [-i IDENTITY]
                keywords [keywords ...]

Quickly SSH to EC2 instances by name

positional arguments:
  keywords              Keyword(s) to filter list of servers, i.e. 'core 21a'

optional arguments:
  -h, --help            show this help message and exit
  -r REGION, --region REGION
                        Overrides the default AWS region.
  -u USER, --user USER  Specifies a user for SSH.
  -i IDENTITY, --identity IDENTITY
                        Selects a file from which the identity (private key)
                        is read.
  -d, --public-dns      Use public DNS name instead of IP address to connect.
```

## Bash Alternative
Don't want to use Python? Try this little Bash alternative (requires `fzf` and `jq` to be installed):
```bash
function awser() {
    if [[ ! $1 ]]; then
        echo "Must provide a search term, i.e. 'trading'."
        return 1
    fi
    local instances=$(aws ec2 describe-instances --filter Name=tag:Name,Values="*$1*" --query 'Reservations[].Instances[].{Name:Tags[?Key==`Name`].Value,IP:PrivateIpAddress}')
    local instance=$(echo "$instances" | jq '.[] | (.Name | .[]) + ": " + .IP' | sed 's/"//g' | fzf -1 -0 --header "Select an instance" | awk -F": " '{print $2}')
    if [[ $instance ]]; then
        ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $instance
    else
        echo "No match found! Please check the term you provided."
    fi
}
```
