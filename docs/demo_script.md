# Demo Script

1. Start the backend:

```bash
cd backend
fastapi dev app/main.py
```

2. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

3. Open `http://localhost:5173`.

4. Select one or more `.txt`, `.md`, or `.csv` files.

5. Keep or edit the default audit question.

6. Click `开始分析`.

7. Confirm that the page shows:

- AI preliminary audit opinion.
- Parsed file status and preview.
- Empty regulation references because vector retrieval is not implemented in M0+.

8. Confirm uploaded files are saved under `backend/uploads/`.
