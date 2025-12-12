
---

# 📚 **OtakuConnect — Personalized Anime & Manga Recommender**

**OtakuConnect** is a personalized recommendation system built for anime and manga enthusiasts.
The app learns user tastes through **genre preferences**, **ratings**, and **written reviews**, and uses AI-driven embeddings to recommend titles that best match each user’s interests.

The system handles both new users and new manga/anime seamlessly, enabling a smooth cold-start experience. Everything runs on a modern stack including **Streamlit**, **Azure OpenAI**, and **PostgreSQL**.

---

## ✨ **Features**

* **Personalized Recommendations**
  Generates ranked anime/manga suggestions using user embeddings and item embeddings.

* **Cold Start Support**
  New users receive recommendations based on selected genres.
  New manga/anime get embeddings from genre text.

* **AI-Powered Review & Genre Understanding**
  Uses text embeddings to extract meaning from user reviews and item metadata.

* **Simple & Modern UI**
  Streamlit interface for browsing recommendations and viewing details.

* **Robust Backend**
  PostgreSQL database for users, preferences, feedback, and embeddings.

---

## 🧠 **How It Works**

1. User Preferences + Review Text → **User Embedding**
2. Manga/Anime Metadata (Genres, Title) → **Item Embedding**
3. System computes similarity scores using cosine similarity
4. Items are ranked and recommended based on the highest scores
5. Recommendations improve as more feedback is collected

---

## 🛠️ **Tech Stack**

* **Python**
* **Streamlit** (Frontend UI)
* **Azure OpenAI** (Embeddings & NLP)
* **PostgreSQL** (Database)
* **SQLAlchemy / psycopg2** (DB Access)

---

## Clone the repo
```bash
git clone git@github.com:mallick20/anime-guru.git
cd src/OtakuConnect
```

### Set environment variable
Set environment variables according to .env.example

### Installing the requirements
```bash
python -m pip install -r requirements.txt`
```
---

## Database Setup

### Setup postgresql server

### Create the db and tables
`cd src/OtakuConnect`

### Data ingestion
`python data_ingest.py`

--- 

## Run the app
`streamlit run animeApp.py`

---
## Collaborators
- Diksha Phuloria
- Shruti Elangovan
- Anurag Mal

---

## References