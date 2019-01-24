#!/usr/bin/env python3
"""Quickly SSH to EC2 instances by name
"""

import sys
import argparse
import readline  # used by input() for more intuitive editing of input
from subprocess import call
import boto3

session = boto3.session.Session()
AWS_DEFAULT_REGION = session.region_name or 'us-west-2'
SSH_CONNECT_TIMEOUT = 10


def parse_args():
    """
    Parse arguments passed to the command
    """
    parser = argparse.ArgumentParser(
        description="Quickly SSH to EC2 instances by name")

    parser.add_argument(
        'keywords',
        nargs="+",
        help="Keyword(s) to filter list of servers, i.e. 'core 21a'")

    parser.add_argument(
        '-r',
        '--region',
        default=AWS_DEFAULT_REGION,
        help="Overrides the default AWS region.")

    parser.add_argument(
        '-p', '--profile', default=None, help="Specifies which profile to use.")

    parser.add_argument(
        '-u', '--user', default=None, help="Specifies a user for SSH.")

    parser.add_argument(
        '-i',
        '--identity',
        default=None,
        help="Selects a file from which the identity (private key) is read.")

    parser.add_argument(
        '-d',
        '--public-dns',
        action='store_true',
        help="Use public DNS name instead of IP address to connect.")

    return parser.parse_args()


def get_hosts(name_filter, region):
    """Retrieve list of hosts from AWS and parse to a reasonable data structure
    """
    hosts = []
    client = boto3.client('ec2', region_name=region)
    response = client.describe_instances(
        Filters=[{
            'Name': 'tag:Name',
            'Values': [name_filter]
        }, {
            'Name': 'instance-state-name',
            'Values': ['running']
        }])

    for r in response['Reservations']:
        for i in r['Instances']:
            hosts.append([
                i,
                next(x['Value'] for x in i['Tags'] if x['Key'] == 'Name')
            ])
    return hosts


def ssh(ip, user, identity):
    """Helper method to SSH to a host
    """
    ssh_args = [
        "-o", "StrictHostKeyChecking=no", "-o",
        "ConnectTimeout=%s" % SSH_CONNECT_TIMEOUT
    ]

    if identity:
        ssh_args += ["-i", identity]

    if user:
        ssh_args += [user + "@" + ip]
    else:
        ssh_args += [ip]

    return call(["ssh"] + ssh_args)


def main():
    """Main function
    """
    args = parse_args()

    if args.profile:
        boto3.setup_default_session(profile_name=args.profile)

    name_filter = "*"
    for a in args.keywords:
        name_filter += a + "*"

    hosts = get_hosts(name_filter, args.region)

    if not hosts:
        sys.exit("No hosts found matching those keywords.")

    host_name_key = 'PrivateIpAddress'
    if args.public_dns:
        host_name_key = 'PublicDnsName'

    if len(hosts) == 1:
        print("Logging in to %s..." % hosts[0][1])
        ssh(hosts[0][0][host_name_key], args.user, args.identity)
    else:
        choice = None

        for i, host in enumerate(hosts, 1):
            print("{0}) {1} - {2}".format(i, host[1], host[0][host_name_key]))
        print("Enter) exit")

        try:
            choice = int(input("Choose wisely: "))
        except (SyntaxError, NameError, ValueError):
            sys.exit("You chose... poorly")

        if choice == 0 or choice > len(hosts):
            sys.exit("You chose... poorly")
        else:
            print("Logging in to %s..." % hosts[choice - 1][1])
            ssh(hosts[choice - 1][0][host_name_key], args.user, args.identity)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nReceived SIGINT, exiting...")
