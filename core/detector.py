import os

def detect_project_type(folder):
    types = {
        "pygame": False,
        "unreal": False,
        "unity": False,
        "web": False,
        "python": False,
        "cpp": False
    }

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                types["python"] = True

                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        if "pygame" in f.read().lower():
                            types["pygame"] = True
                except:
                    pass

            if file.endswith(".cpp") or file.endswith(".h"):
                types["cpp"] = True

            if file.endswith(".uproject"):
                types["unreal"] = True

            if file.endswith(".cs"):
                types["unity"] = True

            if file.endswith(".html") or file.endswith(".js"):
                types["web"] = True

    return types