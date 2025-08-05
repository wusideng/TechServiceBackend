import uvicorn


from config import is_dev, worker_num, server_port, db_name

# convert is_dev from string to boolean
is_dev = bool(is_dev) == True


def main():
    if is_dev:
        print("dev environment, db:", db_name)
        uvicorn_config = {
            "app": "app.main:app",
            "host": "127.0.0.1",
            "port": server_port,
            "log_level": "debug",
            "reload": True,
            "reload_dirs": ["app"],  # 只监视 app 目录
            "reload_delay": 0.25,
            "reload_includes": ["*.py"],  # 只监视 python 文件
            "reload_excludes": ["*.pyc", "__pycache__"],
            "workers": 1,  # 开发环境单进程,生产环境多进程
        }

    else:
        print("prod environment, db:", db_name)
        uvicorn_config = {
            "app": "app.main:app",
            "host": "0.0.0.0",
            "port": server_port,
            "log_level": "info",
            "workers": worker_num,
        }
    uvicorn.run(**uvicorn_config)


if __name__ == "__main__":
    main()
