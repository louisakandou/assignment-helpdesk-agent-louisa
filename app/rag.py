"""
Modul RAG — mengubah knowledge base menjadi embedding, menyimpannya ke FAISS,
melakukan semantic search, lalu menghasilkan jawaban menggunakan LLM.

Alur ini serupa dengan yang sudah dibangun di Assignment 3 (Semantic Search &
LLM Application) dan Sesi 11 (Building a Simple RAG System) — di assignment ini,
alur tersebut dibungkus menjadi fungsi yang dipanggil oleh router.py.
"""

import os
import pandas as pd
import numpy as np
import faiss
from google import genai  # sesuaikan dengan library Gemini API yang digunakan
from google.genai import types                     # "kotak pengaturan" library Gemini (untuk timeout)
_client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),      # API key dibaca dari environment variable, bukan hardcode
    http_options=types.HttpOptions(timeout=30000), # batas tunggu 30 detik, supaya tidak menggantung
)
KNOWLEDGE_BASE_PATH = "data/it_helpdesk_knowledge_base.csv"
GENERATION_MODEL = "gemini-3.1-flash-lite"   # 3.8-flash sering 503/504 (beban tinggi); lite stabil ~1 detik

# 🔧 TODO: muat knowledge base dan bangun index FAISS saat aplikasi startup
# (bukan di setiap request), agar lebih efisien. Pertimbangkan menggunakan
# FastAPI startup event atau lazy-loading dengan cache sederhana.

_index = None
_documents = None
_df = None


def _get_embedding(text: str):
    result = _client.models.embed_content(
        model="gemini-embedding-001",  # sesuaikan versi model embedding
        contents=text,
    )
    return result.embeddings[0].values


def build_index():
    """
    # TODO: implementasikan pembangunan index FAISS dari knowledge base CSV.
    # Referensi: starter_notebook_semantic_search.ipynb dari Assignment 3,
    # Section 1-4 (load data -> unit retrievable -> embedding -> simpan ke FAISS).
    """
    global _index, _documents, _df

    _df = pd.read_csv(KNOWLEDGE_BASE_PATH)

    _documents = (
        "Pertanyaan: " + _df["question"]
        + "\nJawaban: " + _df["answer"]
    ).tolist()

    embeddings = [_get_embedding(doc) for doc in _documents]

    vectors = np.array(embeddings, dtype="float32")

    _index = faiss.IndexFlatL2(vectors.shape[1])

    _index.add(vectors)

    print(f"Index FAISS siap: {_index.ntotal} dokumen")



def semantic_search(query: str, top_k: int = 3):
    """
    # TODO: implementasikan semantic search terhadap index yang sudah dibangun.
    # Referensi: starter_notebook_semantic_search.ipynb, Section 5.
    """
    if _index is None:
        build_index()

    query_vector = np.array([_get_embedding(query)], dtype="float32")

    distances, indices = _index.search(query_vector, top_k)

    return [_documents[i] for i in indices[0]]


async def answer_from_knowledge_base(query: str) -> str:
    """
    Fungsi yang dipanggil router.py ketika intent = 'faq'.
    Menjalankan semantic search, menyusun prompt dengan context hasil retrieval,
    lalu memanggil LLM untuk menghasilkan jawaban.

    # TODO: implementasikan alur lengkap: semantic_search -> build prompt
    # (Persona/Task/Context/Format, lihat Assignment 3 Section 6) -> panggil LLM.
    """
    hasil = semantic_search(query, top_k=3)
    context = "\n\n".join(hasil)

    prompt = f"""Persona: Kamu adalah asisten Helpdesk IT & HR internal perusahaan yang ramah dan akurat.

Task: Jawab pertanyaan karyawan HANYA berdasarkan informasi di bagian Context.
Abaikan bagian Context yang tidak relevan dengan pertanyaan.
Jika jawabannya tidak ada di Context, katakan dengan jujur bahwa kamu tidak memiliki informasi tersebut,
lalu sarankan karyawan menghubungi tim HR atau IT Support. Jangan mengarang informasi.

Context:
{context}

Format: Jawab dalam Bahasa Indonesia, maksimal 3 kalimat, langsung ke inti.

Pertanyaan karyawan: {query}"""

    response = _client.models.generate_content(    # kirim prompt ke Gemini
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return response.text                           # serahkan teks jawabannya ke router