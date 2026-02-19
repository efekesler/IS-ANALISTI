import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from dotenv import load_dotenv
from openai import OpenAI

# API yükleme
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

urun_listesi = []

# -------------------------
# VERİ EKLEME
# -------------------------
def veri_ekle():
    ay = entry_ay.get()
    urun = entry_urun.get()

    try:
        adet = int(entry_adet.get())
        satis = float(entry_satis.get())
        maliyet = float(entry_maliyet.get())
    except:
        messagebox.showerror("Hata", "Adet tam sayı, satış ve maliyet sayısal olmalı")
        return

    # Aynı ay ve ürün var mı kontrol et
    mevcut_index = None
    for i, veri in enumerate(urun_listesi):
        if veri["ay"] == ay and veri["urun"] == urun:
            mevcut_index = i
            break

    if mevcut_index is not None:
        cevap = modern_soru_dialog(
            root,
            "Kayıt Mevcut",
            f"{ay} ayında {urun} ürünü zaten mevcut.\n\n"
            "Nasıl devam etmek istersiniz?"
        )

        if cevap is None:
            return  # İptal

        elif cevap:  # Üzerine yaz
            urun_listesi.pop(mevcut_index)
            tablo.delete(tablo.get_children()[mevcut_index])

        else:  # Toplayarak ekle
            eski_veri = urun_listesi[mevcut_index]

            adet += eski_veri["adet"]

            # Ortalama birim fiyat hesapla
            satis = ((eski_veri["birim_satis"] * eski_veri["adet"]) +
                     (satis * (adet - eski_veri["adet"]))) / adet

            maliyet = ((eski_veri["birim_maliyet"] * eski_veri["adet"]) +
                       (maliyet * (adet - eski_veri["adet"]))) / adet

            urun_listesi.pop(mevcut_index)
            tablo.delete(tablo.get_children()[mevcut_index])

    toplam_ciro = satis * adet
    toplam_maliyet = maliyet * adet
    toplam_kar = toplam_ciro - toplam_maliyet

    veri = {
        "ay": ay,
        "urun": urun,
        "adet": adet,
        "birim_satis": satis,
        "birim_maliyet": maliyet,
        "ciro": toplam_ciro,
        "maliyet": toplam_maliyet,
        "kar": toplam_kar
    }

    urun_listesi.append(veri)

    tablo.insert("", tk.END, values=(
        ay, urun, adet, round(satis, 2), round(maliyet, 2),
        round(toplam_ciro, 2),
        round(toplam_maliyet, 2),
        round(toplam_kar, 2)
    ))

    entry_ay.delete(0, tk.END)
    entry_urun.delete(0, tk.END)
    entry_adet.delete(0, tk.END)
    entry_satis.delete(0, tk.END)
    entry_maliyet.delete(0, tk.END)

    entry_ay.focus()

def modern_soru_dialog(parent, baslik, mesaj):
    dialog = tk.Toplevel(parent)
    dialog.title(baslik)
    dialog.configure(bg="#111111")
    dialog.geometry("420x220")
    dialog.resizable(False, False)
    dialog.grab_set()  # Modal yapar

    tk.Label(dialog,
             text=mesaj,
             bg="#111111",
             fg="white",
             font=("Segoe UI", 10),
             wraplength=380,
             justify="left").pack(pady=20)

    sonuc = {"cevap": None}

    def evet():
        sonuc["cevap"] = True
        dialog.destroy()

    def hayir():
        sonuc["cevap"] = False
        dialog.destroy()

    def iptal():
        sonuc["cevap"] = None
        dialog.destroy()

    button_frame = tk.Frame(dialog, bg="#111111")
    button_frame.pack(pady=15)

    tk.Button(button_frame, text="Üzerine Yaz",
              command=evet,
              bg="white", fg="black",
              font=("Segoe UI", 9, "bold"),
              relief="flat", width=12).grid(row=0, column=0, padx=8)

    tk.Button(button_frame, text="Toplayarak Ekle",
              command=hayir,
              bg="white", fg="black",
              font=("Segoe UI", 9, "bold"),
              relief="flat", width=14).grid(row=0, column=1, padx=8)

    tk.Button(button_frame, text="İptal",
              command=iptal,
              bg="#333333", fg="white",
              font=("Segoe UI", 9),
              relief="flat", width=10).grid(row=0, column=2, padx=8)

    parent.wait_window(dialog)
    return sonuc["cevap"]

def modern_uyari_dialog(parent, baslik, mesaj):
    dialog = tk.Toplevel(parent)
    dialog.title(baslik)
    dialog.configure(bg="#111111")
    dialog.geometry("380x180")
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog,
             text=mesaj,
             bg="#111111",
             fg="white",
             font=("Segoe UI", 10),
             wraplength=340,
             justify="left").pack(pady=25)

    tk.Button(dialog,
              text="Tamam",
              command=dialog.destroy,
              bg="white",
              fg="black",
              font=("Segoe UI", 10, "bold"),
              relief="flat",
              width=12).pack(pady=10)

    parent.wait_window(dialog)

# -------------------------
# GPT ANALİZ
# -------------------------
def analiz_yap():
    if not urun_listesi:
        modern_uyari_dialog(root, "Uyarı", "Analiz yapabilmek için önce veri eklemelisiniz.")
        return

    prompt = f"""
Aşağıdaki satış verilerini analiz et.
Toplam ciro, toplam maliyet ve toplam kar durumunu hesapla ve değerlendir.
Karlılığı artırmak için net ve maddeli öneriler sun.
Genel geçer tavsiyeler verme.
Ciddi analiz yap ve kar artsın.

{urun_listesi}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Sen profesyonel bir finans analiz uzmanısın. Cevapları net ve maddeli yaz."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        sonuc_text.delete("1.0", tk.END)
        sonuc_text.insert(tk.END, response.choices[0].message.content)

    except Exception as e:
        messagebox.showerror("API Hatası", str(e))


# -------------------------
# ARAYÜZ
# -------------------------
root = tk.Tk()
root.title("Satış Analiz Sistemi")
root.geometry("1250x820")
root.configure(bg="#111111")

style = ttk.Style()
style.theme_use("clam")

style.configure("Treeview",
                background="#1e1e1e",
                foreground="white",
                rowheight=28,
                fieldbackground="#1e1e1e")

style.configure("Treeview.Heading",
                background="#222222",
                foreground="white",
                font=("Segoe UI", 10, "bold"))

style.map("Treeview",
          background=[("selected", "#333333")])

# Başlık
tk.Label(root,
         text="SATIŞ ANALİZİ",
         bg="#111111",
         fg="white",
         font=("Segoe UI", 20, "bold")).pack(pady=20)

# ---------------- INPUT (YAN YANA) ----------------
input_frame = tk.Frame(root, bg="#111111")
input_frame.pack(pady=15)

def modern_label(text, col):
    tk.Label(input_frame,
             text=text,
             bg="#111111",
             fg="white",
             font=("Segoe UI", 10)).grid(row=0, column=col, padx=8)

def modern_entry(col):
    e = tk.Entry(input_frame,
                 bg="#1e1e1e",
                 fg="white",
                 insertbackground="white",
                 font=("Segoe UI", 10),
                 relief="flat",
                 width=18)
    e.grid(row=1, column=col, padx=8)
    return e

modern_label("Ay", 0)
modern_label("Ürün", 1)
modern_label("Adet", 2)
modern_label("Birim Satış Fiyatı", 3)
modern_label("Birim Maliyet", 4)

entry_ay = modern_entry(0)
entry_urun = modern_entry(1)
entry_adet = modern_entry(2)
entry_satis = modern_entry(3)
entry_maliyet = modern_entry(4)

# ENTER geçişleri (soldan sağa)
entry_ay.bind("<Return>", lambda e: entry_urun.focus())
entry_urun.bind("<Return>", lambda e: entry_adet.focus())
entry_adet.bind("<Return>", lambda e: entry_satis.focus())
entry_satis.bind("<Return>", lambda e: entry_maliyet.focus())
entry_maliyet.bind("<Return>", lambda e: veri_ekle())

# ---------------- BUTONLAR ----------------
button_frame = tk.Frame(root, bg="#111111")
button_frame.pack(pady=15)

tk.Button(button_frame, text="Veri Ekle", command=veri_ekle,
          bg="white", fg="black",
          font=("Segoe UI", 10, "bold"),
          relief="flat", width=15).grid(row=0, column=0, padx=15)

tk.Button(button_frame, text="Analiz Yap", command=analiz_yap,
          bg="white", fg="black",
          font=("Segoe UI", 10, "bold"),
          relief="flat", width=15).grid(row=0, column=1, padx=15)

# ---------------- ORTA ALAN (TABLO + AI EŞİT) ----------------
content_frame = tk.Frame(root, bg="#111111")
content_frame.pack(fill="both", expand=True, padx=20, pady=10)

content_frame.rowconfigure(0, weight=1)
content_frame.rowconfigure(1, weight=1)
content_frame.columnconfigure(0, weight=1)

columns = (
    "Ay", "Ürün", "Adet",
    "Birim Satış Fiyatı", "Birim Maliyet",
    "Toplam Ciro", "Toplam Maliyet", "Toplam Kar"
)

# TABLO
table_frame = tk.Frame(content_frame, bg="#111111")
table_frame.grid(row=0, column=0, sticky="nsew", pady=10)

tablo = ttk.Treeview(table_frame, columns=columns, show="headings")

for col in columns:
    tablo.heading(col, text=col)
    tablo.column(col, width=140, anchor="center")

scrollbar_table = ttk.Scrollbar(table_frame, orient="vertical", command=tablo.yview)
tablo.configure(yscrollcommand=scrollbar_table.set)

tablo.pack(side="left", fill="both", expand=True)
scrollbar_table.pack(side="right", fill="y")

# AI ANALİZİ
ai_frame = tk.Frame(content_frame, bg="#111111")
ai_frame.grid(row=1, column=0, sticky="nsew", pady=10)

tk.Label(ai_frame,
         text="AI ANALİZİ",
         bg="#111111",
         fg="white",
         font=("Segoe UI", 14, "bold")).pack(pady=5)

text_container = tk.Frame(ai_frame, bg="#111111")
text_container.pack(fill="both", expand=True)

sonuc_text = tk.Text(text_container,
                     bg="#1e1e1e",
                     fg="white",
                     insertbackground="white",
                     font=("Segoe UI", 11),
                     relief="flat",
                     wrap="word")

scrollbar_text = ttk.Scrollbar(text_container, orient="vertical", command=sonuc_text.yview)
sonuc_text.configure(yscrollcommand=scrollbar_text.set)

sonuc_text.pack(side="left", fill="both", expand=True)
scrollbar_text.pack(side="right", fill="y")

root.mainloop()
