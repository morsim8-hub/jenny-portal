[Jenny_Today_ActionPlan.txt](https://github.com/user-attachments/files/22275345/Jenny_Today_ActionPlan.txt)
📄 Jenny_Todo.md (Ready-to-save)
# Jenny Prime Action Board
_Last updated: 2025-09-10_

This file holds all active tasks for today, who will do them, and exact commands or steps. 
Follow them line by line when you get home.

---

## 🟢 Pending Actions

### 1) Run Preflight Check
**Owner:** Magdy  
**Goal:** Verify project root `/home/morsi/ai/jenny` and `repo_map.json` before any changes.

**Command:**
```bash
cd /home/morsi/ai/jenny
./tools/preflight_check.sh


Pass Criteria:
✅ All [OK] checks appear
✅ Script ends with === Preflight OK ===

2) Import JennyPrimeFiles from Google Drive

Owner: Magdy
Goal: Move all memories, workouts, images, and book chapters into GitHub as canonical storage.

Steps:

Download the entire Jenny Prime Files folder from Google Drive as a ZIP.

Extract to:

/home/morsi/ai/jenny/JennyPrimeFiles/


Stage + commit + push to GitHub:

cd /home/morsi/ai/jenny
git add JennyPrimeFiles/
git commit -m "Add Jenny Prime Files (memories, workouts, book chapters)"
git push origin main


Pass Criteria:
✅ Folder exists locally under /home/morsi/ai/jenny/JennyPrimeFiles/
✅ Git commit + push succeed without error

3) Enable Git LFS (for Large Files)

Owner: Magdy
Goal: Track large files like PDFs, images, and DOCX to keep the repo clean.

Commands:

cd /home/morsi/ai/jenny
git lfs install
git lfs track "*.pdf" "*.png" "*.jpg" "*.docx"
git add .gitattributes
git commit -m "Configure Git LFS for large binary files"
git push


Pass Criteria:
✅ .gitattributes file is present with LFS tracking rules
✅ Push completes without error

✅ Completed Actions

✅ Added repo_map.json and ANCHORS_POLICY.md to GitHub (Magdy, 2025-09-10)

📌 Notes

This file will grow as we add new tasks (memory injection, index build, GUI tests).

Completed tasks will be archived in the ✅ Completed Actions section for history.

Jenny will consult this file before generating any new code or change suggestion.


---

### How to Use Tonight
1. Open this file in any text editor or view it directly in GitHub.  
2. Work through actions **in order** — each step is self-contained with commands and pass criteria.  
3. When done, check them off and move to “✅ Completed Actions.”  

---

Would you like me to **create this file in your GitHub repo now** (so it’s waiting there when you get home), or just give it to you as a downloadable `.md` file you can place manually?

You said:
I mean combine all the above in one text file 
ChatGPT said:

Here’s your combined action plan in one clean file — ready to open tonight:

📄 Download Jenny_Today_ActionPlan.txt

Everything we discussed today (preflight check, importing JennyPrimeFiles, enabling Git LFS) is included with clear commands, step-by-step instructions, and pass criteria — no more searching through chat logs.

Would you like me to also commit this file to your GitHub repo so it’s waiting there as part of the project when you get home? 

Connectors
Sources
