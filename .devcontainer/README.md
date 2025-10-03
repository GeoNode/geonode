
How to develop using devcontainers in VSCode
--------------------------------------------



You can develop using the vscode remote containers extension. In this approach you need to:

- Install the extension in your vscode: [ms-vscode-remote.remote-containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

- On your command pallet, select: “Remote-Containers: Reopen in Container”

- If it’s the first time, vscode will take care of building the images. This might take some time.

- Then a new vscode window will open, and it’ll be connected to your docker container.

- The message “Dev Container: Debug Docker Compose” will appear in the bottom-left corner of that window.

- In the vscode terminal, you’re going to see something similar to root@77e80acc89b8:/usr/src/geonode#.

- To run your application, you can use the integrated terminal (./manage.py runserver 0.0.0.0:8000) or the vscode “Run and Debug” option. For launching with “Run and Debug”, generate the following files in the `.vscode` folder inside the `.devcontainer` folder

launch.json
```json
{
    "version": "0.2.0",
    "configurations": [
        
        {
            "name": "Python Debugger: Django",
            "type": "debugpy",
            "request": "launch",
            "args": [
                "runserver",
                "0.0.0.0:8000"
            ],
            "django": true,
            "autoStartBrowser": false,
            "justMyCode": false,
            "program": "/usr/src/geonode/manage.py"
        }
    ]
}
```


The .devcontainer folder should look like this


```
.devcontainer
├── .env
├── .vscode
│   └── launch.json
├── devcontainer.json
├── docker-compose.yml

```