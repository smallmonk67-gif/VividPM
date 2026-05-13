class PackageInstaller:
    def get_missing_backends(self):
        """Return a list of backend IDs that are installable but not currently available."""
        import platform
        import shutil
        system_os = platform.system()
        missing = []
        # Accessing the INSTALLABLE_BACKENDS map from the module scope
        from vivid_gui.installer import INSTALLABLE_BACKENDS
        for backend_id, info in INSTALLABLE_BACKENDS.items():
            os_req = info.get("os", "Linux")
            if isinstance(os_req, str):
                os_req = [os_req]
                
            if system_os not in os_req and "Universal" not in os_req:
                continue
                
            if shutil.which(info["binary"]) is None:
                missing.append(backend_id)
        return missing

    def install(self, pkg, backend):
        return True

    def remove(self, pkg, backend):
        return True

    def install_backend(self, backend_id, terminal="alacritty", on_finish=None):
        import threading
        import time
        import subprocess
        from vivid_gui.installer import INSTALLABLE_BACKENDS
        info = INSTALLABLE_BACKENDS.get(backend_id)
        if not info: return

        def worker():
            try:
                import platform
                cmd = info["install_cmd"]
                is_gui_or_echo = cmd[0] in ["open", "xdg-open", "echo"]
                
                if platform.system() == "Windows":
                    if is_gui_or_echo:
                        proc = subprocess.Popen(cmd, shell=True)
                    else:
                        proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    if is_gui_or_echo:
                        if cmd[0] == "open" and platform.system() == "Linux":
                            cmd[0] = "xdg-open"
                        proc = subprocess.Popen(cmd)
                    else:
                        import os
                        import stat
                        import shlex
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        scratch_dir = os.path.join(os.path.dirname(current_dir), "scratch")
                        os.makedirs(scratch_dir, exist_ok=True)
                        script_path = os.path.join(scratch_dir, f"install_{backend_id}.sh")
                        
                        safe_cmd = shlex.join(cmd)
                        script_content = f"#!/bin/bash\necho 'Target: {info['display_name']}'\n{safe_cmd}\nsleep 2\n"
                        with open(script_path, "w") as f: f.write(script_content)
                        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)
                        proc = subprocess.Popen([terminal, "-e", script_path])
                
                proc.wait()
                for cmd in info["post_install"]:
                    try: subprocess.run(cmd, check=False)
                    except: pass
                time.sleep(1.0)
                if on_finish: on_finish()
            except Exception as e:
                print(f"[installer] install error: {e}")

        threading.Thread(target=worker, daemon=True).start()
