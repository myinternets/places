import platform
import sys

python_major = sys.version_info.major
python_minor = sys.version_info.minor
python_version = f"{python_major}{python_minor}"
os_name = platform.system().lower()
arch = platform.machine()


def generate_torch_url(package_name, version):
    global os_name
    global arch
    global python_version
    if arch == 'x86_64':
        arch = 'amd64' if os_name == 'windows' else 'x86_64'
    elif arch == 'aarch64':
        arch = 'arm64'

    if os_name == 'darwin':
        os_name = 'macosx_10_9' if arch == 'x86_64' else 'macosx_11_0'

    base_url = "https://download.pytorch.org/whl/cpu"

    if package_name == "torch":
        if os_name.startswith('macosx'):
            url = f"{base_url}/{package_name}-{version}-cp{python_version}-none-{os_name}_{arch}.whl"
        else:
            url = f"{base_url}/{package_name}-{version}%2Bcpu-cp{python_version}-cp{python_version}-{os_name}_{arch}.whl"
    elif package_name == "torchvision":
        if os_name.startswith('macosx'):
            url = f"{base_url}/{package_name}-{version}-cp{python_version}-cp{python_version}-{os_name}_{arch}.whl"
        else:
            url = f"{base_url}/{package_name}-{version}%2Bcpu-cp{python_version}-cp{python_version}-{os_name}_{arch}.whl"
    else:
        raise ValueError(f"Unknown package name: {package_name}")

    return url


def get_pip_command(package_name, urls):
    # return pip install command for all urls with no cache (for dockerfile)
    return f"pip install --no-cache-dir {' '.join(urls)}"

def main(pip_requirements_path="torch-requirements.txt"):
    urls = []
    urls.append(generate_torch_url("torch", "2.0.0"))
    urls.append(generate_torch_url("torchvision", "0.15.2"))
    # print(get_pip_command("torch", urls))
    with open(f"{pip_requirements_path}", "w") as f:
        f.write('\n'.join(urls))
        f.write('\n')
    print(f"Python: {python_major}.{python_minor}\nArch: {arch}\nOS: {os_name}")
    print(f"\n..generated [{pip_requirements_path}]")
    # print("\nProceed to run the following now:\n")
    # print(f"pip install --no-cache-dir -r {pip_requirements_path}")

if __name__ == "__main__":
    pip_gen_file = "torch-requirements.txt"
    main(pip_gen_file)
