# ACEIRO — Personal Work Hours Tracker

> [!Warning]  
> Tool development assisted with AI (Claude Code on VSC).

## What Is It?

I basically got fed up trying to find a simple tracker that would just allow me to record hours worked (in my regular work and the tasks that fall out from the sky), categorise some of those hours and then tally it up at the end.

Most trackers either record only tasks, more like a to-do, and more advanced ones are aimed at freelancers for billable hours and such.

This is just a simple application to run on your computer (Windows), featuring:

* **Shift Start/End Stopwatch:** Track your daily work sessions effortlessly.
* **Manual Task Entry:** Log tasks specifying Date, Type (*Current Work* / *Ad Hoc Work*), Task Name, and Hours.
* **Automatic Shift Allocation:** Shift hours automatically cover tasks already logged for that day; remaining time is marked as "Unspecified".

<img width="1398" height="822" alt="image" src="https://github.com/user-attachments/assets/621f8612-a0f2-4e0c-a8db-30d68ed525f5" />

* **Monthly Report:** Includes a dropdown filter to view *All Months* (from the start of your logs) or an individual month (defaults to the current month), along with a *All / Current Work / Ad Hoc Work* toggle:
* Selecting **Current Work** or **Ad Hoc Work** displays hours logged for that specific category and its percentage relative to total worked hours in the selected period (Expected Hours and Balance apply only to total hours, so they are hidden here).
* Below the chart, a ranking highlights the tasks with the most logged hours.

<img width="1380" height="772" alt="image" src="https://github.com/user-attachments/assets/64ba7fe7-9cfe-4ab0-a03d-8b6a2b6f27fa" />



* **Expected vs. Worked Hours Comparison:** Expected hours are calculated at **7 hours per business day** with recorded activity (no need to specify contracted hours anywhere). Weekends and Portuguese national holidays are automatically detected from the calendar and excluded from expected hours. Next to the entry form, a **Day Classification** toggle (*Business Day / Overtime*) allows for exceptions — such as working on a holiday or taking a weekday off. Worked hours on these days count normally toward *Worked Hours*; the toggle only dictates whether they add to *Expected Hours*.

<img width="1374" height="1065" alt="image" src="https://github.com/user-attachments/assets/60c8a538-cdcf-40c0-977b-c5fe9eb4b36a" />


* **CSV Import/Export:** Compatible with Excel.
* **Multi-user Support:** Manage multiple profiles within a single installation — useful for tracking a small team (2–3 people) from one place, with each person maintaining their own isolated data. See **Multi-user Support** below.

Your data is stored locally in `dados-<username>.json` files within the app folder (one per profile). No external server is involved, and no internet connection is required after installation (the initial run requires internet only to download required libraries and fonts).

---

## First-time Setup

In theory, running the .exe package should require no additional setup. However, if it fails:

1. **Install Python:** If Python is not yet installed, download it from [python.org/downloads](https://www.python.org/downloads/). During installation, make sure to check the box **"Add python.exe to PATH"**.
2. **Launch the App:** Double-click `IniciarAceiro.bat` inside the app folder using File Explorer. **Do not** type the filename into a Command Prompt window; always launch it via double-click.
* *Note: The first launch takes a bit longer as it sets up the environment. Subsequent launches open almost instantly.*


3. **WebView2 Runtime:** If Windows prompts for permission regarding **WebView2 Runtime** (a Microsoft component used to display the GUI window), accept it. It is free and typically pre-installed on recent Windows 10/11 builds.

---

## Multi-user Support (For Small Teams)

Aceiro supports separate profiles within the same installation, allowing you and 2–3 colleagues to maintain distinct hour logs, reports, and Expected/Worked/Balance metrics without data overlapping.

The first time Aceiro opens on a specific computer, a **"Who are you?"** prompt asks you to select or create your profile. It never assumes a default profile — even if others exist — to prevent cross-contamination when sharing folders. Once selected, that computer remembers your profile choice and launches into it directly on subsequent runs. Each computer maintains its own profile selection locally without affecting other machines.

* **Switch Profiles:** Use the **User** selector next to the stopwatch.
* **Create a Profile:** Click **+ New User** (or the **Create / Enter** button on the home screen), type a name, and confirm. The profile starts with a clean slate.

Each profile writes to its own `dados-<username>.json` file within the app folder (see [Where Data Is Stored](https://www.google.com/search?q=%23where-data-is-stored)). These files sync automatically when placed in a shared OneDrive or SharePoint folder. However, the local active profile selection is stored outside this folder, ensuring colleagues sharing a synced directory can select their own active profiles without overriding yours.


## Share with Colleagues (Single Standalone Executable)

To share Aceiro with colleagues who do not have Python installed or prefer not to manage batch files and scripts, you can build a single, portable executable (`Aceiro.exe`) yourself (instead of using the one I already give you, because why not.

### How to Build and Share

1. **Generate the Executable:** On your computer (where Python is already installed and working), double-click `ConstruirExeParaColegas.bat`. This process takes 1–2 minutes and only needs to be performed once. The compiled file will appear at `dist\Aceiro.exe`.
2. **Distribute:** Send `dist\Aceiro.exe` to your team via Email, Microsoft Teams, USB drive, or OneDrive. No auxiliary folders or dependencies are required.
3. **Run:** Colleagues can place `Aceiro.exe` anywhere (e.g., Desktop) and double-click to run. It creates its local data file adjacent to the executable on its first run.

> **Important Windows Security Notice**
> Because `Aceiro.exe` is an internal utility without a paid digital signature, Windows SmartScreen may display a blue warning screen (*"Windows protected your PC"*) on its first launch — especially if sent via email or web transfer. Advise colleagues to click **"More info"** and then select **"Run anyway"**.
> Corporate antivirus tools may also flag unknown executables; if blocked, request IT to whitelist the file. Standalone executables may also take 1–2 seconds longer to launch than script-based setups.
>
> There's also the equivalent .sh version for Linux users.

---

## Multi-Device Usage (OneDrive / SharePoint)

You can place the entire application folder inside a synced OneDrive or SharePoint directory and run the initial setup on each computer. The virtual environment folder (`venv`) is deliberately excluded from syncing, whereas `dados-<username>.json` and `utilizadores.json` will sync across devices.

### Best Practices for Synced Folders

* **Avoid Simultaneous Usage:** Always close Aceiro on one machine before launching it on another. Ensure your OneDrive icon displays a green checkmark (sync complete) before opening the app on a secondary device to avoid sync conflicts.
* **File Check-Out:** If using a SharePoint document library, utilize the **Check-Out** feature on JSON data files to physically prevent simultaneous access across devices.

---

## Where Data Is Stored

* **User Data:** Each profile maintains a dedicated JSON file within the root directory (e.g., `dados-john.json`, `dados-jane.json`).
* **User Directory:** A lightweight `utilizadores.json` file stores the shared list of profile names.
* **Exports:** Clicking **Export CSV** generates a `aceiro-export-<username>.csv` file formatted for Excel in the main directory for the currently selected profile.

All stored files use plain human-readable text and can be backed up, copied, or opened with standard text editors.

