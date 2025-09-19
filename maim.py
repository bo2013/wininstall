import os, requests, sys, tempfile, shutil

def getsource():
    sources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources")
    wininstall_pwd_sources = os.path.join(os.getcwd(), "wininstall_pwd_sources")

    result = []
    if os.path.exists(sources):
        with open(sources, encoding="utf-8") as f:
            result.extend(f.read().splitlines())

    if os.path.exists(wininstall_pwd_sources):
        with open(wininstall_pwd_sources, encoding="utf-8") as f:
            result.extend(f.read().splitlines())

    return result


def install(package, sources):
    for source in sources:
        url = f"{source}/packages/{package[0]}/{package}/package".replace("//", "/").replace("https:/", "https://").replace("http:/", "http://")
        print(f"Get: {url}...", end="")

        try:
            res = requests.get(url, timeout=10)
        except requests.RequestException as e:
            print(f" Fail ({e})")
            continue

        if res.status_code != 200:
            print(f" Fail ({res.status_code})")
            continue

        print(" Ok")
        file = [line.strip() for line in res.text.splitlines() if line.strip()]

        try:
            name = next(line.split(":", 1)[1].strip() for line in file if line.lstrip().startswith("N:"))
            download = next(line.split(":", 1)[1].strip() for line in file if line.lstrip().startswith("D:"))
            install_cmd = next(line.split(":", 1)[1].strip() for line in file if line.lstrip().startswith("I:"))
        except StopIteration:
            print(" Manifest invalid")
            continue

        print(f"Downloading {name} from {download}...")
        try:
            with requests.get(download, stream=True, timeout=30) as r:
                r.raise_for_status()
        
                # Try to get filename from Content-Disposition header
                filename = None
                cd = r.headers.get("Content-Disposition")
                if cd and "filename=" in cd:
                    filename = cd.split("filename=")[1].strip('" ')
        
                # If not available, get filename from URL
                if not filename:
                    filename = os.path.basename(download.split("?")[0])
        
                # If still not available, fallback to default
                if not filename:
                    filename = "package.bin"
        
                suffix = os.path.splitext(filename)[1]  # get file extension
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            tmp.write(chunk)
                    temp_path = tmp.name
        except requests.RequestException as e:
            print(f" Download failed ({e})")
            continue


        print(f"Installing {name}...")
        cmd = install_cmd.replace("$downloaded$", temp_path)
        os.system(cmd)

        # Remove temporary file after installation
        try:
            os.remove(temp_path)
        except Exception:
            pass

        # If installed successfully from one source, exit the loop
        break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python installer.py <package>")
        sys.exit(1)

    install(sys.argv[1], getsource())
