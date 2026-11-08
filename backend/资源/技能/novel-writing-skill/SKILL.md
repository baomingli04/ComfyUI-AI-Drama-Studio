---
name: novel-writing
description: AI-assisted novel writing skill — covers project management, world-building, character design, plot control, volume/chapter outlines, manuscript drafting, chapter reviews, style control, and prompt templates.
---

# 📖 Novel Writing Skill

A comprehensive AI-assisted novel writing system covering the full lifecycle from world-building to manuscript production and review.

---

## Skill Overview

This skill organizes a novel project into **10 modular components**, each stored in its own directory. Follow the numbering order for a top-down workflow: set up the project → build the world → create characters → plan the plot → outline volumes → outline chapters → draft manuscripts → review chapters → enforce style → use prompt templates.

---

## Directory Structure

```
writing-skill/
├── SKILL.md                        # This file — master instructions
├── 00_project_control/             # Project metadata & global settings
│   └── README.md
├── 01_world_settings/              # World-building & setting details
│   └── README.md
├── 02_characters/                  # Character profiles & relationships
│   └── README.md
├── 03_plot_control/                # Main plot arcs & story beats
│   └── README.md
├── 04_volume_outlines/             # Volume-level outlines (macro structure)
│   └── README.md
├── 05_chapter_outlines/            # Chapter-level outlines (micro structure)
│   └── README.md
├── 06_manuscripts/                 # Drafted chapter manuscripts
│   └── README.md
├── 07_chapter_reviews/             # Review notes & revision records
│   └── README.md
├── 08_style_control/               # Writing style guides & tone rules
│   └── README.md
└── 09_prompt_templates/            # Reusable prompt templates for AI
    └── README.md
```

---

## Module Instructions

### 00 — Project Control
- Store **project-level metadata**: title, author, genre, target audience, word-count goals, deadlines, and status tracking.
- Maintain a `project.yaml` or `project.json` as the single source of truth.
- All other modules should reference this file for global settings.

### 01 — World Settings
- Define the **world and setting**: geography, history, magic/technology systems, cultures, languages, factions, religions, calendar, and key locations.
- Use separate files per topic (e.g., `magic_system.md`, `geography.md`) for large worlds.
- Keep a `world_overview.md` as a quick-reference summary.

### 02 — Characters
- Create **character profiles**: name, age, appearance, personality, backstory, motivations, abilities, relationships, and character arc.
- Maintain a `character_list.md` index file linking to individual character files.
- Track **relationship maps** (text or diagram) to visualize connections.

### 03 — Plot Control
- Define the **macro plot**: core conflict, theme, three-act (or custom) structure, major turning points, climax, and resolution.
- List **sub-plots** and their intersections with the main plot.
- Maintain a **timeline** of key plot events.

### 04 — Volume Outlines
- Break the novel into **volumes** (or parts/books if multi-volume).
- Each volume file should contain: title, synopsis, chapter range, key events, and emotional arc.
- Name files like `vol_01.md`, `vol_02.md`, etc.

### 05 — Chapter Outlines
- Create a detailed outline **per chapter**: chapter number, title, POV character, setting, scene list, goals, key dialogue beats, and hooks.
- Name files like `ch_001.md`, `ch_002.md`, etc.
- Include a `chapter_index.md` summarizing all chapters.

### 06 — Manuscripts
- Store **drafted text** for each chapter.
- Name files like `ch_001_draft.md`, `ch_001_v2.md`, etc., to track versions.
- Keep manuscripts as clean prose; avoid inline editing notes (use `07_chapter_reviews` for that).

### 07 — Chapter Reviews
- After drafting, create a **review file** per chapter: summary of issues, continuity checks, pacing analysis, dialogue quality, emotional impact, and revision suggestions.
- Name files like `review_ch_001.md`.
- Track review status: `pending → in-review → revised → approved`.

### 08 — Style Control
- Define **writing style rules**: narrative voice (first-person, third-person, etc.), tense, tone, sentence length preferences, vocabulary level, forbidden words/phrases, and stylistic references.
- Include example passages that demonstrate the target style.
- Optionally maintain a **style checklist** for self-review.

### 09 — Prompt Templates
- Store **reusable prompt templates** for common AI-assisted tasks:
  - Drafting a chapter from an outline
  - Expanding a scene
  - Writing dialogue
  - Describing a setting
  - Reviewing a chapter
  - Generating character backstory
  - Brainstorming plot twists
- Each template should include: purpose, required inputs (variables), and the prompt text with placeholders like `{{chapter_outline}}`, `{{character_name}}`, etc.

---

## Workflow

1. **Initialize**: Fill out `00_project_control` with project metadata.
2. **World-build**: Populate `01_world_settings` with all setting details.
3. **Characters**: Create profiles in `02_characters`.
4. **Plot**: Lay out the macro plot in `03_plot_control`.
5. **Volume Outline**: Break the story into volumes in `04_volume_outlines`.
6. **Chapter Outline**: Detail each chapter in `05_chapter_outlines`.
7. **Draft**: Write manuscripts in `06_manuscripts`, referencing outlines and using `09_prompt_templates`.
8. **Review**: Evaluate drafts in `07_chapter_reviews`, applying rules from `08_style_control`.
9. **Revise**: Update manuscripts based on reviews; repeat steps 7–8 until approved.
10. **Finalize**: Mark chapters as approved; update project status.

---

## Rules & Conventions

- **Language**: All content files should be written in the same language as the novel unless otherwise specified.
- **File Naming**: Use lowercase with underscores. Prefix chapter files with zero-padded numbers (e.g., `ch_001`).
- **Consistency**: Always cross-reference `00_project_control` and `01_world_settings` before drafting to ensure consistency.
- **Version Control**: Never overwrite a manuscript; create a new version file instead.
- **Reviews**: Every chapter must go through at least one review cycle before being marked as approved.
