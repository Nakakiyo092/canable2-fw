import subprocess
import os

def main():
    folder_name = "build_cmake"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Directory '{folder_name}' created.")
    else:
        print(f"Directory '{folder_name}' already exists.")

    os.chdir(folder_name)
    print(f"Changed directory to '{os.getcwd()}'")

    # cmake
    try:
        command = ['cmake', '-G', 'MinGW Makefiles', '..']
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
            for line in process.stdout:
                print(line, end='')

            return_code = process.wait()
            if return_code == 0:
                print("CMake command executed successfully.")
            else:
                print(f"CMake command failed with return code {return_code}")

    except FileNotFoundError:
        print("CMake command not found. Ensure CMake is installed and available in PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # make
    try:
        command = ['make', '-j10']
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
            for line in process.stdout:
                print(line, end='')

            return_code = process.wait()
            if return_code == 0:
                print("make -j10 command executed successfully.")
            else:
                print(f"make -j10 command failed with return code {return_code}")

    except FileNotFoundError:
        print("make -j10 command not found. Ensure make is installed and available in PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
