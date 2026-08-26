import subprocess
import json
import argparse
import os


def get_system_info(port):
    key = os.path.expanduser("~/.ssh/id_ed25519")

    command = (
        "echo OS=$(cat /etc/os-release | grep '^PRETTY_NAME=' | cut -d= -f2-); "
        "echo CPU=$(nproc); "
        "echo MEMORY=$(free -h | awk '/Mem:/ {print $2}'); "
        "echo DISK=$(df -h / | awk 'NR==2 {print $2}')"
    )

    result = subprocess.run(
        [
            "ssh",
            "-i", key,
            "-o", "PreferredAuthentications=publickey",
            "-o", "PasswordAuthentication=no",
            "-p", str(port),
            "root@127.0.0.1",
            command
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return result.stdout.strip()

    return "unavailable"



def check_ssh(port):
    key = os.path.expanduser("~/.ssh/id_ed25519")

    result = subprocess.run(
        [
            "ssh",
            "-i", key,
            "-o", "PreferredAuthentications=publickey",
            "-o", "PasswordAuthentication=no",
            "-p", str(port),
            "root@127.0.0.1",
            "echo connected"
        ],
        capture_output=True,
        text=True
    )

    return result.returncode == 0

ports = {
        "debian-ssh-1": 2221,
        "debian-ssh-2": 2222
        }

def get_instances():
    result = subprocess.run(
        ["unikraft", "instance", "ls"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    lines = result.stdout.strip().splitlines()
    servers = []

    for line in lines[1:]:
        parts = line.split()

        if len(parts) < 3:
            continue

        server = ({
            "name": parts[1],
            "state": parts[2],
            "health": "healthy" if parts[2] == "running" else "down"
        })

        port = ports.get(server["name"])

        if port:
            server["ssh"] = "healthy" if check_ssh(port) else "down"
            server["system"] = get_system_info(port)
        servers.append(server)

    return servers



def main():
    parser = argparse.ArgumentParser(
        description="Check Unikraft instance health"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output"
    )

    parser.add_argument(
        "--output",
        default="report.json",
        help="JSON report filename"
    )

    args = parser.parse_args()

    try:
        servers = get_instances()
    except Exception as error:
        print(f"ERROR: {error}")
        return 1

    with open(args.output, "w") as file:
        json.dump(servers, file, indent=2)

    if args.json:
        print(json.dumps(servers, indent=2))
    else:
        for server in servers:
            print(
                f"{server['name']}: "
                f"{server['state']} - "
                f"{server['health']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
