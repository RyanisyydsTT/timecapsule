# Deployment
## Hi from Ryan, this docs will guide you how to host this onto any OS using ``uv`` and ``Cloudflare Tunnel``

### Step One
> Please clone the project by command line or downloading through GitHub website as ZIP file and unarchive it.
```bash
git clone https://github.com/RyanisyydsTT/timecapsule
```

### Step Two
> Please install uv to your OS.
> Linux/macOS/Windows WSL(Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
> Windows (Powershell)
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup a Cloudflare account
> Follow the guides from Hack Club's RaspAPI's docs. You can choose creating a tunnel with trycloudflare.com or on your own domain using Cloudflare Zero Trust

### Create a forward policy
> Edit your config.yml if you're using cloudflared, or from Zero Trust's dashboard. Forward HTTP port ``8000`` to the internet.

### Run your service!
> Start your terminal app. For Windows: Press WIN+R and type ``powershell`` and continue; For macOS or Linux, open your terminal app. Set your working path to the server folder.
> EX: Folder is in ~/Desktop/timecapsule/; execute ``cd ~/Desktop/timecapsule/``.

> Start your server by typing ``uv run main.py``


```
```
```
```
```
```
