# Time Capsule
> Time Capsule is a API service made w/ FastAPI, just as it’s name, it stores your story into a secured capsule database, once it’s the unlock day, send a GET request to get your memories!!

## Usage

> ### Obtain Token
> **Obtains a token for you**
> Endpoint: ``/obtain``
> Type: POST

> Scheme:
```json
  {
      "username": "ryanisyyds"
  }
```
```
> ```
> Response:
   ```json
{
    "success": true,
    "message": "account created!",
    "token": "SENSORED"
}
> ```


> ### Store
> **Stores your capsule**
> Endpoint: `/store`
> Type: POST
> Scheme:
```json
{
    "content": "Hello",
    "unlock_at": "2026/7/5"
}
> ```
> Authorization: Bearer TOKEN

> Response:
```json
{
   "success": true,
   "message": "Capsule stored successfully"
}
```

> ### List
> **Lists your capsules**
> Endpoint: ``/list``
> Type: GET

> Authorization: Bearer TOKEN

> Response:
```json
 [
     {
         "id": "26cae396-8c0e-4214-83d2-25c9bd664364",
         "created_at": "2026-04-19T05:04:58.077734+00:00",
         "unlock_at": "2026-07-05"
     },
     {
         "id": "de201d30-f210-4993-868d-c6a87e9e1ca4",
         "created_at": "2026-04-18T09:13:24.673784+00:00",
         "unlock_at": "2026-07-05"
     }
 ]
```

>  ### Stats
> **Shows how many capsules has been created at this server**
> Endpoint: ``/stats``
> Type: GET

> Authorization: Bearer TOKEN

> Response:
```json
{
    "time": "2026-04-19T05:15:44.901043+00:00",
    "counts": 2
}
```

## Contributing
> This repository is using MIT license. Feel free to make a Pull Request or submit an issue!
