# Rag Contest API

## For Users
### Get a list of contests available
```
curl -X GET {ip}:{port}/api/contests \
    -H "x-api-key: {Your-API-Key}"
```

### Get contest information
```
curl -X GET {ip}:{port}/api/contests/{contest_id} \
    -H "x-api-key: {Your-API-Key}"
```

### Get a question
```
curl -X GET {ip}:{port}/api/questions/{question_id} \
    -H "x-api-key: {Your-API-Key}"
```

### Get all questions of a contest
```
```

### Submit your answer
```
curl -X POST {ip}:{port}/api/questions/{question_id} \
    -H "x-api-key: {Your-API-Key}" \
    -H "Content-Type: application/json" \
    -d '{"answer": "I am fine"}'
```

## For Developers
