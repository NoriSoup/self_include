import os
import sys
import zipfile
import urllib.request
import shutil
import subprocess
from pathlib import Path

# 配置参数
PYTHON_VERSION = "3.10.9"  # 可更改为你需要的Python版本
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
MINGIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/MinGit-2.41.0.3-64-bit.zip"

INSTALL_DIR = Path(".") / "bin"
PYTHON_DIR = INSTALL_DIR / f"python-{PYTHON_VERSION}"
GIT_DIR = INSTALL_DIR / "MinGit"


def download_and_extract(url, target_dir):
    """下载并解压zip文件到目标目录"""
    print(f"正在下载 {url}...")
    zip_path = INSTALL_DIR / "temp.zip"

    # 创建目录
    target_dir.mkdir(parents=True, exist_ok=True)

    # 下载文件
    urllib.request.urlretrieve(url, zip_path)

    # 解压文件
    print(f"正在解压到 {target_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    # 删除临时文件
    zip_path.unlink()


def configure_python():
    """配置嵌入式Python"""
    # 修改pythonXX._pth文件以包含site-packages
    pth_file = next(PYTHON_DIR.glob("python*._pth"))
    with open(pth_file, 'r+') as f:
        content = f.read()
        if "import site" not in content:
            f.write("\nimport site\n")

    # 创建site-packages目录
    site_packages = PYTHON_DIR / "site-packages"
    site_packages.mkdir(exist_ok=True)


def add_to_path(env_file, path_to_add):
    """将路径添加到环境变量文件中"""
    path_to_add = str(path_to_add.resolve())
    with open(env_file, 'a') as f:
        f.write(f'\nSET PATH={path_to_add};%PATH%')


def create_launcher_scripts():
    """创建启动脚本"""
    # 创建Python启动脚本
    with open(INSTALL_DIR / "python_cli.bat", 'w') as f:
        f.write(f"""@echo off
SET PYTHONHOME=%~dp0\\python-{PYTHON_VERSION}
SET PATH=%~dp0\\python-{PYTHON_VERSION};%~dp0\\MinGit\\cmd;%PATH%
"%~dp0\\python-{PYTHON_VERSION}\\python.exe" %*
""")

    # 创建Git启动脚本
    with open(INSTALL_DIR / "git_cli.bat", 'w') as f:
        f.write("""@echo off
SET PATH=%~dp0\\MinGit\\cmd;%~dp0\\python-{PYTHON_VERSION};%PATH%
"%~dp0\\MinGit\\cmd\\git.exe" %*
""")


def install_pip():
    """为嵌入式Python安装pip"""
    print("正在安装pip...")
    get_pip = INSTALL_DIR / "get-pip.py"
    urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", get_pip)

    subprocess.run([
        str(PYTHON_DIR / "python.exe"),
        str(get_pip),
        "--no-warn-script-location"
    ], check=True)

    get_pip.unlink()


def main():
    print("开始设置嵌入式环境...")

    # 清理并创建安装目录
    if INSTALL_DIR.exists():
        shutil.rmtree(INSTALL_DIR)
    INSTALL_DIR.mkdir()

    try:
        # 下载并安装嵌入式Python
        download_and_extract(PYTHON_EMBED_URL, PYTHON_DIR)
        configure_python()

        # 下载并安装MinGit
        download_and_extract(MINGIT_URL, GIT_DIR)

        # 创建启动脚本
        create_launcher_scripts()

        # 安装pip
        install_pip()

        print(f"\n安装完成！嵌入式环境已创建在 {INSTALL_DIR}")
        print("你可以使用以下命令:")
        print(f"  {INSTALL_DIR}\\python_cli.bat - 运行Python")
        print(f"  {INSTALL_DIR}\\git_cli.bat - 运行Git")

        # 创建环境变量配置文件
        env_file = INSTALL_DIR / "set_env.bat"
        add_to_path(env_file, PYTHON_DIR)
        add_to_path(env_file, GIT_DIR / "cmd")
        print(f"\n运行 {env_file} 可以临时设置环境变量")

    except Exception as e:
        print(f"安装过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()