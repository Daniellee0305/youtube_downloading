"""
YouTube Playlist Downloader
Apple-inspired GUI with 9 themes, cover/thumbnail support,
flexible folder + file naming templates, and detailed progress.
Built with CustomTkinter + yt-dlp.
"""

import os, re, threading, io, glob
import urllib.request
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox
import yt_dlp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FF = "Segoe UI"
MF = "Consolas"

# ═══════════════════════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════════════════════

def _t(swatch, bg, s1, s2, brd, acc, ach, ac2, tx, td, ok, er, wr,
       re_, ro, rh, sel, tb, tt):
    return {"swatch":swatch,"bg":bg,"surface":s1,"surface2":s2,"border":brd,
            "accent":acc,"accent_hover":ach,"accent2":ac2,"text":tx,
            "text_dim":td,"success":ok,"error":er,"warning":wr,
            "row_even":re_,"row_odd":ro,"row_hover":rh,"selected":sel,
            "tag_bg":tb,"tag_text":tt}

THEMES = {
    "Light": _t("#007aff","#ffffff","#f5f5f7","#eeeeef","#d2d2d7",
                "#007aff","#0066d6","#34aadc","#1d1d1f","#86868b",
                "#248a3d","#d70015","#b25000",
                "#ffffff","#f9f9f9","#eeeeef","#dce8f8","#e4eaf4","#005ec4"),
    "Dark": _t("#8e8e93","#1c1c1e","#2c2c2e","#3a3a3c","#48484a",
               "#8e8e93","#a1a1a6","#a1a1a6","#f5f5f7","#8e8e93",
               "#30d158","#ff453a","#ffd60a",
               "#2c2c2e","#323234","#3a3a3c","#3a3a4c","#3a3a48","#b0b0c0"),
    "Midnight": _t("#6e6eff","#000000","#111111","#1a1a1a","#2a2a2a",
                   "#6e6eff","#8585ff","#32d7d1","#f5f5f7","#86868b",
                   "#30d158","#ff453a","#ffd60a",
                   "#111111","#161616","#222222","#1c1c3e","#222244","#a5a5ff"),
    "Ocean": _t("#0a84ff","#000000","#0c1117","#141d26","#1e2d3d",
                "#0a84ff","#409cff","#64d2ff","#f5f5f7","#86868b",
                "#30d158","#ff453a","#ffd60a",
                "#0c1117","#101920","#182530","#0a2a4a","#0e2540","#64d2ff"),
    "Sunset": _t("#ff6f3c","#0a0606","#140e0b","#1e1410","#2e2018",
                 "#ff6f3c","#ff8a5c","#ffb340","#f5f5f7","#86868b",
                 "#30d158","#ff453a","#ffd60a",
                 "#140e0b","#1a1210","#261a14","#2e1a10","#2e1e14","#ffb340"),
    "Rose": _t("#ff375f","#080406","#140c10","#1e1218","#301a24",
               "#ff375f","#ff6482","#ff6baf","#f5f5f7","#86868b",
               "#30d158","#ff453a","#ffd60a",
               "#140c10","#1a1014","#26161e","#2e1020","#2e1424","#ff6baf"),
    "Lavender": _t("#bf5af2","#060408","#120e18","#1a1422","#281e36",
                   "#bf5af2","#d07ff8","#da8fff","#f5f5f7","#86868b",
                   "#30d158","#ff453a","#ffd60a",
                   "#120e18","#16101e","#201828","#241838","#221636","#da8fff"),
    "Forest": _t("#30d158","#040804","#0a140a","#101e10","#1a2e1a",
                 "#30d158","#54e07a","#66e8a0","#f5f5f7","#86868b",
                 "#30d158","#ff453a","#ffd60a",
                 "#0a140a","#0e1a0e","#142414","#0e2e16","#102e18","#66e8a0"),
    "Arctic": _t("#007aff","#f5f5f7","#ffffff","#f0f0f2","#d2d2d7",
                 "#007aff","#0066d6","#147ce5","#1d1d1f","#86868b",
                 "#248a3d","#d70015","#b25000",
                 "#ffffff","#fafafa","#f0f0f2","#e0ecfa","#e8eef8","#0055b3"),
}
DEFAULT_THEME = "Midnight"

# ─── Constants ───────────────────────────────────────────────────────────────

AUDIO_FORMATS = ["MP3","AAC","WAV","FLAC","OGG","OPUS","M4A"]
VIDEO_FORMATS = ["MP4","MKV","WEBM"]
ALL_FORMATS   = AUDIO_FORMATS + VIDEO_FORMATS
AUDIO_CODEC   = {"MP3":"mp3","AAC":"aac","WAV":"wav","FLAC":"flac",
                 "OGG":"vorbis","OPUS":"opus","M4A":"m4a"}
VID_EXT       = {"MP4":"mp4","MKV":"mkv","WEBM":"webm"}
BITRATES      = ["Original","64 kbps","96 kbps","128 kbps","160 kbps",
                 "192 kbps","256 kbps","320 kbps"]
RESOLUTIONS   = ["Original","360p","480p","720p","1080p","1440p","2160p (4K)"]
RES_V = {"Original":"Original","360p":"360p","480p":"480p","720p":"720p","1080p":"1080p",
         "1440p":"1440p","2160p (4K)":"2160p"}
FRAMERATES    = ["Original","24 fps","30 fps","60 fps"]
FR_V = {"Original":"Original","24 fps":"24","30 fps":"30","60 fps":"60"}
VBR = {("360p","24"):800,("360p","30"):1000,("360p","60"):1500,
       ("480p","24"):1500,("480p","30"):2000,("480p","60"):3000,
       ("720p","24"):2000,("720p","30"):2500,("720p","60"):3750,
       ("1080p","24"):4000,("1080p","30"):5000,("1080p","60"):7500,
       ("1440p","24"):8000,("1440p","30"):10000,("1440p","60"):15000,
       ("2160p","24"):16000,("2160p","30"):20000,("2160p","60"):30000}

TOKEN_MAP = {
    "{title}":"%(track,title|NA)s", "{author}":"%(artist,creator,uploader,channel|NA)s",
    "{number}":"%(playlist_index,track_number,track_index|0)s",
    "{number2}":"%(playlist_index,track_number,track_index|0)02d", "{number3}":"%(playlist_index,track_number,track_index|0)03d",
    "{playlist}":"%(playlist_title,playlist,album|NA)s",
    "{date}":"%(release_date,upload_date>%Y-%m-%d,date|NA)s", "{year}":"%(release_year,upload_date>%Y|NA)s",
    "{id}":"%(id)s",
}
TOKENS = ["{title}","{author}","{number}","{number2}","{number3}",
          "{playlist}","{date}","{year}","{id}"]
DEFAULT_FILE_TMPL   = "{number2}. {title}"
DEFAULT_FOLDER_TMPL = "{playlist}"
DEFAULT_EP_TMPL     = "{number2} - {title}"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def is_audio(f): return f.upper() in AUDIO_FORMATS
def bps(l): return -1 if l=="Original" else int(l.split()[0])
def fmt_dur(s):
    if s is None: return "--:--"
    h,r=divmod(int(s),3600); m,sec=divmod(r,60)
    return f"{h}:{m:02}:{sec:02}" if h else f"{m}:{sec:02}"
def fmt_size(b):
    if b<0: return "—"
    for u in ("B","KB","MB","GB"):
        if b<1024: return f"{b:.1f} {u}"
        b/=1024
    return f"{b:.1f} TB"
def est_size(dur,fmt,bitrate,vres,vfps):
    if dur is None or dur<=0: return -1
    fu=fmt.upper()
    if is_audio(fu):
        if bitrate < 0: bitrate = 128
        r=1411 if fu=="WAV" else (1411*0.6 if fu=="FLAC" else bitrate)
        return dur*r*1000/8
    if vres=="Original": vres="1080p"
    if vfps=="Original": vfps="30"
    vbr=VBR.get((vres,vfps),5000)
    return dur*(vbr+128)*1000/8
def tok_to_yt(t):
    r=t
    for k,v in TOKEN_MAP.items(): r=r.replace(k,v)
    return r
def preview(t,idx=3,title="File Name",author="Author Name",
            pl="My Playlist",date="2009-10-25",vid="dQw4w9WgXcQ"):
    reps={"{title}":title,"{author}":author,"{number}":str(idx),
          "{number2}":f"{idx:02d}","{number3}":f"{idx:03d}",
          "{playlist}":pl,"{date}":date,"{year}":date[:4],"{id}":vid}
    r=t
    for k,v in reps.items(): r=r.replace(k,v)
    return r
def sanitize(n): return re.sub(r'[<>:"/\\|?*]','',n).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# VideoRow
# ═══════════════════════════════════════════════════════════════════════════════

class VideoRow(ctk.CTkFrame):
    def __init__(self, master, i, title, dur, url, on_toggle, t, **kw):
        bg=t["row_even"] if i%2==0 else t["row_odd"]
        super().__init__(master, fg_color=bg, corner_radius=10, height=44, **kw)
        self.grid_columnconfigure(2, weight=1)
        self.url=url; self.duration_sec=dur; self.title_text=title
        self.original_index = i
        self.selected=ctk.BooleanVar(value=False)
        self._bg=bg; self._t=t; self._on_toggle=on_toggle

        self.cb=ctk.CTkCheckBox(self,text="",variable=self.selected,width=20,height=20,
            fg_color=t["accent"],hover_color=t["accent_hover"],
            border_color=t["border"],corner_radius=5,command=self._tog)
        self.cb.grid(row=0,column=0,padx=(12,6),pady=6)

        ctk.CTkLabel(self,text=f"{i+1}.",width=30,
            font=ctk.CTkFont(family=FF,size=12,weight="bold"),
            text_color=t["text_dim"]).grid(row=0,column=1,padx=(0,4),sticky="w")

        ctk.CTkLabel(self,text=title,font=ctk.CTkFont(family=FF,size=13),
            text_color=t["text"],anchor="w").grid(row=0,column=2,padx=(0,8),sticky="we")

        ctk.CTkLabel(self,text=fmt_dur(dur),font=ctk.CTkFont(family=FF,size=11),
            text_color=t["text_dim"],fg_color=t["surface2"],
            corner_radius=8,width=56,height=20).grid(row=0,column=3,padx=(0,4),pady=6)

        self.size_lbl=ctk.CTkLabel(self,text="—",width=68,
            font=ctk.CTkFont(family=FF,size=11),text_color=t["accent2"],
            fg_color=t["surface2"],corner_radius=8,height=20)
        self.size_lbl.grid(row=0,column=4,padx=(0,4),pady=6)

        self.status_lbl=ctk.CTkLabel(self,text="",width=100,
            font=ctk.CTkFont(family=FF,size=11),text_color=t["text_dim"])
        self.status_lbl.grid(row=0,column=5,padx=(0,12),pady=6)

        self.info_lbl=ctk.CTkLabel(self,text="",width=20,font=ctk.CTkFont(size=12))
        self.info_lbl.grid(row=0,column=6,padx=(0,8))

        self.bind("<Enter>",lambda _: self.configure(fg_color=t["row_hover"]) if not self.selected.get() else None)
        self.bind("<Leave>",lambda _: self.configure(fg_color=t["selected"] if self.selected.get() else self._bg))

    def _tog(self):
        self._on_toggle()
        self.configure(fg_color=self._t["selected"] if self.selected.get() else self._bg)
    def set_sel(self,v):
        self.selected.set(v)
        self.configure(fg_color=self._t["selected"] if v else self._bg)
    def set_status(self,txt,color=None):
        self.status_lbl.configure(text=txt,text_color=color or self._t["text_dim"])
    def update_size(self,b):
        self.size_lbl.configure(text=fmt_size(b) if b>=0 else "—")
        
    def set_hover_info(self, ctk_im, txt):
        self.info_lbl.configure(text="ℹ️", text_color=self._t["accent2"], cursor="hand2")
        self.hover_win = None
        
        def on_enter(e):
            if self.hover_win: return
            self.hover_win = ctk.CTkToplevel(self.winfo_toplevel())
            self.hover_win.overrideredirect(True)
            self.hover_win.attributes("-topmost", True)
            
            x = self.info_lbl.winfo_rootx() - 180
            y = self.info_lbl.winfo_rooty() + 25
            self.hover_win.geometry(f"+{x}+{y}")
            
            f = ctk.CTkFrame(self.hover_win, fg_color=self._t["surface"], 
                             border_color=self._t["border"], border_width=1, corner_radius=8)
            f.pack(fill="both", expand=True)
            
            if ctk_im:
                ctk.CTkLabel(f, text="", image=ctk_im).pack(padx=10, pady=(10,4))
            ctk.CTkLabel(f, text=txt, font=ctk.CTkFont(family=FF, size=11, weight="bold"),
                         text_color=self._t["text"]).pack(padx=10, pady=(0,10))
            
        def on_leave(e):
            if self.hover_win:
                self.hover_win.destroy()
                self.hover_win = None
                
        self.info_lbl.bind("<Enter>", on_enter)
        self.info_lbl.bind("<Leave>", on_leave)


# ═══════════════════════════════════════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Playlist Downloader")
        self.geometry("1080x900")
        self.minsize(720,500)
        self._rows=[]
        self._entries=[]
        self._downloading=False
        self._vol=[]        # video-only labels
        self._vow=[]        # video-only widgets
        self._pl_title="Playlist"
        self._theme=DEFAULT_THEME
        self._t=THEMES[DEFAULT_THEME]
        self._cancel_download=False
        self.configure(fg_color=self._t["bg"])
        self._build()

    def _apply_theme(self,name):
        if name not in THEMES: return
        self._theme=name; self._t=THEMES[name]
        for w in self.winfo_children(): w.destroy()
        self._rows.clear(); self._vol.clear(); self._vow.clear()
        self.configure(fg_color=self._t["bg"])
        self._build()

    # ── Factories ────────────────────────────────────────────────────────────

    def _dd(self,p,var,vals,w=120):
        t=self._t
        return ctk.CTkOptionMenu(p,variable=var,values=vals,width=w,height=30,
            font=ctk.CTkFont(family=FF,size=12),fg_color=t["surface2"],
            button_color=t["accent"],button_hover_color=t["accent_hover"],
            text_color=t["text"],dropdown_fg_color=t["surface2"],
            dropdown_text_color=t["text"],dropdown_hover_color=t["accent"],
            corner_radius=8)

    def _lbl(self,p,txt,r,c,vo=False):
        t=self._t
        l=ctk.CTkLabel(p,text=txt,font=ctk.CTkFont(family=FF,size=11,weight="bold"),
            text_color=t["text_dim"])
        l.grid(row=r,column=c,sticky="w",padx=(0,12),pady=(0,3))
        if vo: self._vol.append(l)
        return l

    def _heading(self,p,txt):
        return ctk.CTkLabel(p,text=txt,
            font=ctk.CTkFont(family=FF,size=13,weight="bold"),
            text_color=self._t["text"])

    def _sep(self,p,r):
        ctk.CTkFrame(p,fg_color=self._t["border"],height=1
            ).grid(row=r,column=0,columnspan=20,sticky="we",pady=8)

    def _tok_buttons(self,parent,entry_widget,var,callback):
        t=self._t
        f=ctk.CTkFrame(parent,fg_color="transparent")
        ctk.CTkLabel(f,text="Tokens:",font=ctk.CTkFont(family=FF,size=10),
            text_color=t["text_dim"]).pack(side="left",padx=(0,4))
        for tok in TOKENS:
            ctk.CTkButton(f,text=tok,height=22,width=len(tok)*7+14,
                font=ctk.CTkFont(family=MF,size=10),
                fg_color=t["tag_bg"],hover_color=t["accent"],
                text_color=t["tag_text"],corner_radius=5,
                command=lambda tk=tok,e=entry_widget,v=var,cb=callback:
                    self._insert_tok(e,v,tk,cb)
            ).pack(side="left",padx=1,pady=1)
        return f

    def _insert_tok(self,entry,var,tok,cb):
        pos=entry.index("insert"); cur=var.get()
        var.set(cur[:pos]+tok+cur[pos:])
        entry.icursor(pos+len(tok))
        cb()

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build(self):
        t=self._t

        # ── Bottom bar (FIRST → never hidden) ────────────────────────────────
        bot=ctk.CTkFrame(self,fg_color=t["surface"],corner_radius=0,height=100)
        bot.pack(side="bottom",fill="x")
        bot.pack_propagate(False)

        # Top row: download status
        status_row=ctk.CTkFrame(bot,fg_color="transparent")
        status_row.pack(fill="x",padx=20,pady=(8,0))

        self.dl_status_lbl=ctk.CTkLabel(status_row,text="Ready",
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text_dim"],anchor="w")
        self.dl_status_lbl.pack(side="left",fill="x",expand=True)

        self.pct_lbl=ctk.CTkLabel(status_row,text="",
            font=ctk.CTkFont(family=FF,size=12,weight="bold"),
            text_color=t["accent2"])
        self.pct_lbl.pack(side="right")

        # Progress bar
        self.progress=ctk.CTkProgressBar(bot,height=8,
            fg_color=t["surface2"],progress_color=t["accent"],corner_radius=4)
        self.progress.set(0)
        self.progress.pack(fill="x",padx=20,pady=(6,0))

        # Bottom row: folder picker + download button
        bot_row=ctk.CTkFrame(bot,fg_color="transparent")
        bot_row.pack(fill="x",padx=20,pady=(8,8))

        ctk.CTkLabel(bot_row,text="Save to:",
            font=ctk.CTkFont(family=FF,size=11),
            text_color=t["text_dim"]).pack(side="left",padx=(0,4))

        self.dest_var=ctk.StringVar(value=os.path.join(os.getcwd(),"Downloads"))
        ctk.CTkEntry(bot_row,textvariable=self.dest_var,height=30,
            font=ctk.CTkFont(family=FF,size=12),fg_color=t["surface2"],
            border_color=t["border"],text_color=t["text"],corner_radius=8
        ).pack(side="left",fill="x",expand=True,padx=(0,4))

        ctk.CTkButton(bot_row,text="📁",width=32,height=30,corner_radius=8,
            fg_color=t["surface2"],hover_color=t["border"],text_color=t["text"],
            command=self._browse).pack(side="left",padx=(0,10))

        self.stop_btn=ctk.CTkButton(bot_row,text="Stop",
            width=80,height=34,corner_radius=10,
            font=ctk.CTkFont(family=FF,size=13,weight="bold"),
            fg_color=t["error"],hover_color=t["error"],
            command=self._on_stop)
        # We don't pack stop_btn yet

        self.dl_btn=ctk.CTkButton(bot_row,text="Download Selected",
            width=170,height=34,corner_radius=10,
            font=ctk.CTkFont(family=FF,size=13,weight="bold"),
            fg_color=t["accent"],hover_color=t["accent_hover"],
            command=self._on_download)
        self.dl_btn.pack(side="right")

        # ── Scrollable content ───────────────────────────────────────────────
        self.content=ctk.CTkScrollableFrame(self,fg_color=t["bg"],corner_radius=0,
            scrollbar_button_color=t["border"],
            scrollbar_button_hover_color=t["accent"])
        self.content.pack(fill="both",expand=True)
        self.content.grid_columnconfigure(0,weight=1)
        cr=0  # current row

        # ── Header + themes ──────────────────────────────────────────────────
        hdr=ctk.CTkFrame(self.content,fg_color="transparent")
        hdr.grid(row=cr,column=0,sticky="we",padx=24,pady=(16,4)); cr+=1
        hdr.grid_columnconfigure(0,weight=1)

        ctk.CTkLabel(hdr,text="YouTube Playlist Downloader",
            font=ctk.CTkFont(family=FF,size=24,weight="bold"),
            text_color=t["text"]).grid(row=0,column=0,sticky="w")
        ctk.CTkLabel(hdr,text="powered by yt-dlp",
            font=ctk.CTkFont(family=FF,size=12),
            text_color=t["text_dim"]).grid(row=1,column=0,sticky="w")

        # Theme swatches
        th_f=ctk.CTkFrame(hdr,fg_color="transparent")
        th_f.grid(row=0,column=1,rowspan=2,sticky="e")
        ctk.CTkLabel(th_f,text="Theme",font=ctk.CTkFont(family=FF,size=11),
            text_color=t["text_dim"]).pack(side="left",padx=(0,8))
        for nm,th in THEMES.items():
            sc=th["swatch"]; active=(nm==self._theme)
            ctk.CTkButton(th_f,text="",width=24,height=24,corner_radius=12,
                fg_color=sc,hover_color=sc,
                border_width=3 if active else 0,
                border_color=t["text"] if active else sc,
                command=lambda n=nm: self._apply_theme(n)).pack(side="left",padx=2)

        ctk.CTkFrame(self.content,fg_color=t["border"],height=1
            ).grid(row=cr,column=0,sticky="we",padx=24,pady=(4,8)); cr+=1

        # ── URL bar ──────────────────────────────────────────────────────────
        uf=ctk.CTkFrame(self.content,fg_color="transparent")
        uf.grid(row=cr,column=0,sticky="we",padx=24); cr+=1
        uf.grid_columnconfigure(0,weight=1)

        self.url_entry=ctk.CTkEntry(uf,height=38,
            placeholder_text="Paste playlist URL here…",
            font=ctk.CTkFont(family=FF,size=13),fg_color=t["surface"],
            border_color=t["border"],text_color=t["text"],corner_radius=10)
        self.url_entry.grid(row=0,column=0,sticky="we",padx=(0,8))

        self.fetch_btn=ctk.CTkButton(uf,text="Fetch",width=90,height=38,
            font=ctk.CTkFont(family=FF,size=13,weight="bold"),
            fg_color=t["accent"],hover_color=t["accent_hover"],
            corner_radius=10,command=self._on_fetch)
        self.fetch_btn.grid(row=0,column=1)

        # ── Card 1: Format & Quality ─────────────────────────────────────────
        c1=ctk.CTkFrame(self.content,fg_color=t["surface"],corner_radius=14,
            border_color=t["border"],border_width=1)
        c1.grid(row=cr,column=0,sticky="we",padx=24,pady=(10,0)); cr+=1

        s=ctk.CTkFrame(c1,fg_color="transparent")
        s.pack(fill="x",padx=18,pady=12)
        for c in range(4): s.grid_columnconfigure(c,weight=1)

        self._lbl(s,"Format",0,0)
        self.fmt_var=ctk.StringVar(value="MP3")
        self.fmt_var.trace_add("write",lambda*_: self._on_set())
        self.fmt_menu=self._dd(s,self.fmt_var,ALL_FORMATS,110)
        self.fmt_menu.grid(row=1,column=0,sticky="w",padx=(0,8))

        self._lbl(s,"Audio Bitrate",0,1)
        self.bps_var=ctk.StringVar(value="Original")
        self.bps_var.trace_add("write",lambda*_: self._on_set())
        self.bps_menu=self._dd(s,self.bps_var,BITRATES,110)
        self.bps_menu.grid(row=1,column=1,sticky="w",padx=(0,8))

        self._lbl(s,"Resolution",0,2,vo=True)
        self.res_var=ctk.StringVar(value="Original")
        self.res_var.trace_add("write",lambda*_: self._on_set())
        self.res_menu=self._dd(s,self.res_var,RESOLUTIONS,120)
        self.res_menu.grid(row=1,column=2,sticky="w",padx=(0,8))
        self._vow.append(self.res_menu)

        self._lbl(s,"Frame Rate",0,3,vo=True)
        self.fps_var=ctk.StringVar(value="Original")
        self.fps_var.trace_add("write",lambda*_: self._on_set())
        self.fps_menu=self._dd(s,self.fps_var,FRAMERATES,90)
        self.fps_menu.grid(row=1,column=3,sticky="w")
        self._vow.append(self.fps_menu)

        self.fmt_info=ctk.CTkLabel(s,text="",font=ctk.CTkFont(family=FF,size=11),
            text_color=t["text_dim"])
        self.fmt_info.grid(row=2,column=0,columnspan=4,sticky="w",pady=(6,0))

        # ── Card 2: Options ──────────────────────────────────────────────────
        c_opt=ctk.CTkFrame(self.content,fg_color=t["surface"],corner_radius=14,
            border_color=t["border"],border_width=1)
        c_opt.grid(row=cr,column=0,sticky="we",padx=24,pady=(8,0)); cr+=1

        opt_inner=ctk.CTkFrame(c_opt,fg_color="transparent")
        opt_inner.pack(fill="x",padx=18,pady=12)

        self._heading(opt_inner,"Cover Options").grid(row=0,column=0,sticky="w",
            columnspan=4,pady=(0,8))

        self.dl_thumb_var=ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_inner,text="Download cover/thumbnail image",
            variable=self.dl_thumb_var,
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text"],
            fg_color=t["accent"],hover_color=t["accent_hover"],
            border_color=t["border"],corner_radius=5
        ).grid(row=1,column=0,sticky="w",padx=(0,24))

        self.embed_thumb_var=ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_inner,text="Embed cover in audio/video file",
            variable=self.embed_thumb_var,
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text"],
            fg_color=t["accent"],hover_color=t["accent_hover"],
            border_color=t["border"],corner_radius=5
        ).grid(row=1,column=1,sticky="w")

        # ── Card 3: Folder & Naming ──────────────────────────────────────────
        c2=ctk.CTkFrame(self.content,fg_color=t["surface"],corner_radius=14,
            border_color=t["border"],border_width=1)
        c2.grid(row=cr,column=0,sticky="we",padx=24,pady=(8,0)); cr+=1

        n=ctk.CTkFrame(c2,fg_color="transparent")
        n.pack(fill="x",padx=18,pady=12)
        n.grid_columnconfigure(1,weight=1)

        # ── Folder structure ─────────────────────────────────────────────────
        self._heading(n,"Folder Structure").grid(row=0,column=0,sticky="w",
            columnspan=6,pady=(0,6))

        # Playlist folder
        self.use_pl_folder=ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(n,text="Playlist folder:",variable=self.use_pl_folder,
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text"],
            fg_color=t["accent"],hover_color=t["accent_hover"],
            border_color=t["border"],corner_radius=5,
            command=self._on_folder).grid(row=1,column=0,sticky="w",padx=(0,6))

        self.pl_folder_var=ctk.StringVar(value=DEFAULT_FOLDER_TMPL)
        self.pl_folder_entry=ctk.CTkEntry(n,textvariable=self.pl_folder_var,
            height=28,font=ctk.CTkFont(family=MF,size=12),
            fg_color=t["surface2"],border_color=t["border"],
            text_color=t["text"],corner_radius=8)
        self.pl_folder_entry.grid(row=1,column=1,sticky="we",padx=(0,6),columnspan=5)
        self.pl_folder_entry.bind("<KeyRelease>",lambda _: self._upd_preview())

        # Token row for playlist folder
        self.pl_tok_frame=self._tok_buttons(n,self.pl_folder_entry,self.pl_folder_var,self._upd_preview)
        self.pl_tok_frame.grid(row=2,column=0,columnspan=6,sticky="w",pady=(2,6))

        # Episode subfolder
        self.use_ep_folder=ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(n,text="Episode subfolder:",variable=self.use_ep_folder,
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text"],
            fg_color=t["accent"],hover_color=t["accent_hover"],
            border_color=t["border"],corner_radius=5,
            command=self._on_folder).grid(row=3,column=0,sticky="w",padx=(0,6))

        self.ep_folder_var=ctk.StringVar(value=DEFAULT_EP_TMPL)
        self.ep_folder_entry=ctk.CTkEntry(n,textvariable=self.ep_folder_var,
            height=28,font=ctk.CTkFont(family=MF,size=12),
            fg_color=t["surface2"],border_color=t["border"],
            text_color=t["text"],corner_radius=8)
        self.ep_folder_entry.grid(row=3,column=1,sticky="we",padx=(0,6),columnspan=5)
        self.ep_folder_entry.bind("<KeyRelease>",lambda _: self._upd_preview())

        self.ep_tok_frame=self._tok_buttons(n,self.ep_folder_entry,self.ep_folder_var,self._upd_preview)
        self.ep_tok_frame.grid(row=4,column=0,columnspan=6,sticky="w",pady=(2,6))

        ctk.CTkLabel(n,text="Single-video downloads skip subfolders automatically.",
            font=ctk.CTkFont(family=FF,size=11),text_color=t["text_dim"]
        ).grid(row=5,column=0,columnspan=6,sticky="w",pady=(0,6))

        self._sep(n,6)

        # ── File naming ──────────────────────────────────────────────────────
        self._heading(n,"File Name").grid(row=7,column=0,sticky="w",
            columnspan=6,pady=(0,6))

        tmpl_row=ctk.CTkFrame(n,fg_color="transparent")
        tmpl_row.grid(row=8,column=0,columnspan=6,sticky="we")
        tmpl_row.grid_columnconfigure(0,weight=1)

        self.file_var=ctk.StringVar(value=DEFAULT_FILE_TMPL)
        self.file_entry=ctk.CTkEntry(tmpl_row,textvariable=self.file_var,height=30,
            font=ctk.CTkFont(family=MF,size=13),fg_color=t["surface2"],
            border_color=t["border"],text_color=t["text"],corner_radius=8)
        self.file_entry.grid(row=0,column=0,sticky="we",padx=(0,6))
        self.file_entry.bind("<KeyRelease>",lambda _: self._upd_preview())

        ctk.CTkButton(tmpl_row,text="Reset",width=55,height=30,corner_radius=8,
            font=ctk.CTkFont(family=FF,size=11),fg_color=t["surface2"],
            hover_color=t["border"],text_color=t["text_dim"],
            command=lambda: (self.file_var.set(DEFAULT_FILE_TMPL),self._upd_preview())
        ).grid(row=0,column=1)

        self.file_tok_frame=self._tok_buttons(n,self.file_entry,self.file_var,self._upd_preview)
        self.file_tok_frame.grid(row=9,column=0,columnspan=6,sticky="w",pady=(4,4))

        # Preview
        self.preview_lbl=ctk.CTkLabel(n,text="",
            font=ctk.CTkFont(family=MF,size=11),text_color=t["accent2"],anchor="w")
        self.preview_lbl.grid(row=10,column=0,columnspan=6,sticky="w",pady=(2,0))

        # ── Toolbar ──────────────────────────────────────────────────────────
        tb=ctk.CTkFrame(self.content,fg_color="transparent")
        tb.grid(row=cr,column=0,sticky="we",padx=24,pady=(10,3)); cr+=1
        tb.grid_columnconfigure(2,weight=1)

        ctk.CTkButton(tb,text="Select All",width=85,height=26,corner_radius=8,
            font=ctk.CTkFont(family=FF,size=12),fg_color=t["surface2"],
            hover_color=t["border"],text_color=t["text"],
            command=self._sel_all).grid(row=0,column=0,padx=(0,4))

        ctk.CTkButton(tb,text="Deselect",width=75,height=26,corner_radius=8,
            font=ctk.CTkFont(family=FF,size=12),fg_color=t["surface2"],
            hover_color=t["border"],text_color=t["text"],
            command=self._desel).grid(row=0,column=1,padx=(0,8))

        self.count_lbl=ctk.CTkLabel(tb,text="0 / 0 selected",
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text_dim"])
        self.count_lbl.grid(row=0,column=2,sticky="w")

        self.total_lbl=ctk.CTkLabel(tb,text="",
            font=ctk.CTkFont(family=FF,size=12,weight="bold"),text_color=t["accent2"])
        self.total_lbl.grid(row=0,column=4,sticky="e")
        ctk.CTkLabel(tb,text="Est. total:",
            font=ctk.CTkFont(family=FF,size=12),text_color=t["text_dim"]
        ).grid(row=0,column=3,sticky="e",padx=(0,4))

        # ── Video list ───────────────────────────────────────────────────────
        self.list_box=ctk.CTkFrame(self.content,fg_color=t["surface"],
            corner_radius=14,border_color=t["border"],border_width=1)
        self.list_box.grid(row=cr,column=0,sticky="nswe",padx=24,pady=(3,16)); cr+=1
        self.list_box.grid_columnconfigure(0,weight=1)
        self.content.grid_rowconfigure(cr-1,weight=1)

        self.placeholder=ctk.CTkLabel(self.list_box,
            text="Paste a playlist URL above and press Fetch",
            font=ctk.CTkFont(family=FF,size=14),text_color=t["text_dim"])
        self.placeholder.grid(row=0,column=0,pady=50)

        self._on_set()
        self._on_folder()
        self._upd_preview()

    # ── Preview ──────────────────────────────────────────────────────────────

    def _upd_preview(self):
        file_p=preview(self.file_var.get(),pl=self._pl_title)
        fmt=self.fmt_var.get().lower()
        ext=fmt if is_audio(fmt.upper()) else VID_EXT.get(fmt.upper(),fmt)
        path=""
        if self.use_pl_folder.get():
            fp=preview(self.pl_folder_var.get(),pl=self._pl_title)
            path+=sanitize(fp)+"/"
        if self.use_ep_folder.get():
            ep=preview(self.ep_folder_var.get(),pl=self._pl_title)
            path+=sanitize(ep)+"/"
        self.preview_lbl.configure(text=f"→  {path}{file_p}.{ext}")

    def _on_folder(self):
        self.pl_folder_entry.configure(state="normal" if self.use_pl_folder.get() else "disabled")
        self.ep_folder_entry.configure(state="normal" if self.use_ep_folder.get() else "disabled")
        self._upd_preview()

    # ── Settings ─────────────────────────────────────────────────────────────

    def _on_set(self):
        t=self._t; fmt=self.fmt_var.get().upper(); vid=not is_audio(fmt)
        st="normal" if vid else "disabled"
        for w in self._vow: w.configure(state=st)
        for l in self._vol:
            l.configure(text_color=t["text_dim"] if vid else t["border"])
        if fmt=="WAV":
            self.bps_menu.configure(state="disabled")
            self.fmt_info.configure(text="WAV — uncompressed lossless, bitrate ignored")
        elif fmt=="FLAC":
            self.bps_menu.configure(state="disabled")
            self.fmt_info.configure(text="FLAC — compressed lossless, bitrate ignored")
        elif self.bps_var.get() == "Original" or self.res_var.get() == "Original":
            self.bps_menu.configure(state="normal")
            self.fmt_info.configure(text=f"{fmt} container · audio/video original native quality" if vid
                else f"{fmt} · Original Native Quality")
        else:
            self.bps_menu.configure(state="normal")
            self.fmt_info.configure(text=f"{fmt} container · audio ~128 kbps" if vid
                else f"{fmt} · {self.bps_var.get()}")
        self._refresh_sizes()
        self._upd_preview()

    def _refresh_sizes(self):
        fmt=self.fmt_var.get().upper(); b=bps(self.bps_var.get())
        res=RES_V.get(self.res_var.get(),"1080p")
        fps=FR_V.get(self.fps_var.get(),"30")
        st=0
        for r in self._rows:
            e=est_size(r.duration_sec,fmt,b,res,fps)
            r.update_size(e)
            if e>0 and r.selected.get(): st+=e
        self.total_lbl.configure(text=fmt_size(st) if self._rows else "")

    # ── Selection ────────────────────────────────────────────────────────────

    def _upd_count(self):
        s=sum(1 for r in self._rows if r.selected.get())
        self.count_lbl.configure(text=f"{s} / {len(self._rows)} selected")
        self._refresh_sizes()

    def _sel_all(self):
        for r in self._rows: r.set_sel(True)
        self._upd_count()

    def _desel(self):
        for r in self._rows: r.set_sel(False)
        self._upd_count()

    def _browse(self):
        f=filedialog.askdirectory()
        if f: self.dest_var.set(f)

    # ── Fetch ────────────────────────────────────────────────────────────────

    def _clean_url(self, url):
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        new_qs = {k: v for k, v in qs.items() if k in ('v', 'list')}
        if new_qs:
            parsed = parsed._replace(query=urllib.parse.urlencode(new_qs, doseq=True))
            return urllib.parse.urlunparse(parsed)
        return url

    def _show_overlay(self, title, msg, is_error=True):
        t = self._t
        if hasattr(self, '_err_overlay') and self._err_overlay.winfo_exists():
            self._err_overlay.destroy()
            
        color = t["error"] if is_error else t["accent"]
        tl = title.lower()
        if "warning" in tl or "no " in tl or "nothing" in tl:
            color = t["warning"]
        elif "done" in tl or "success" in tl:
            color = t["success"]

        self._err_overlay = ctk.CTkFrame(self, fg_color=t["surface2"], border_color=color, border_width=2, corner_radius=10)
        self._err_overlay.place(relx=0.98, rely=0.98, anchor="se")

        ctk.CTkLabel(self._err_overlay, text=title, font=ctk.CTkFont(family=FF, size=15, weight="bold"), text_color=color).pack(pady=(12, 2), padx=20, anchor="w")
        ctk.CTkLabel(self._err_overlay, text=msg, font=ctk.CTkFont(family=FF, size=12), text_color=t["text"], wraplength=250).pack(pady=(2, 12), padx=20, anchor="w")
        
        self.after(3000, lambda: self._err_overlay.destroy() if hasattr(self, '_err_overlay') and self._err_overlay.winfo_exists() else None)

    def _on_fetch(self):
        url=self.url_entry.get().strip()
        if not url:
            self._show_overlay("No URL","Please enter a playlist URL.", False)
            return
            
        url = self._clean_url(url)
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        
        self.fetch_btn.configure(text="Loading…",state="disabled")
        self._current_fetch_url = url
        self._current_fetch_start = 1
        self._entries = []
        self._pl_title = ""
        self._fetch_chunk()

    def _fetch_chunk(self):
        start = self._current_fetch_start
        end = start + 49
        threading.Thread(target=self._fetch_chunk_w,args=(self._current_fetch_url, start, end),daemon=True).start()

    def _fetch_chunk_w(self, url, start, end):
        opts={"quiet":True,"no_warnings":True,"extract_flat":"in_playlist","skip_download":True,"yes_playlist":True,
              "playliststart": start, "playlistend": end}
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                info=y.extract_info(url,download=False)
        except Exception as e:
            err_msg = str(e)
            self.after(0,lambda m=err_msg: self._fetch_err(m)); return
            
        entries=info.get("entries")
        chunk_len = 0
        if entries is None:
            entries = [info]
            pl = info.get("title", "Video")
            chunk_len = 1
        else:
            existing_pl = getattr(self, "_pl_title", "")
            pl = info.get("title", existing_pl if existing_pl else "Playlist")
            entries = list(entries)
            chunk_len = len(entries)
            
        entries = [e for e in entries if e is not None]
            
        if not entries and start == 1:
            self.after(0,lambda: self._fetch_err("No videos found.")); return
            
        resolved=[{
            "title":e.get("title","Untitled"),
            "url":e.get("url") or e.get("webpage_url") or
                  f"https://www.youtube.com/watch?v={e.get('id','')}",
            "duration":e.get("duration"),"id":e.get("id",""),
        } for e in entries]
        
        self.after(0,lambda: self._append_and_check(resolved, pl, chunk_len))

    def _fetch_err(self,msg):
        self.fetch_btn.configure(text="Fetch",state="normal")
        self._show_overlay("Error",msg, True)
        
        err_lower = msg.lower()
        if "country" in err_lower or "geo-blocked" in err_lower or "region" in err_lower:
            warn_msg = "This video cannot be displayed in your current country.\n\nPlease check the URL or try using a VPN, then re-enter."
        else:
            warn_msg = "Could not fetch the URL.\n\nPlease check the URL and re-enter."
            
        messagebox.showwarning("Fetch Failed", warn_msg)
        self.url_entry.delete(0, "end")
        self.url_entry.configure(placeholder_text="Please re-enter a valid URL...")
        self.url_entry.focus()

    def _append_and_check(self, resolved, pl_title, chunk_len):
        t=self._t
        if not self._pl_title:
            self._pl_title = pl_title
            for w in self.list_box.winfo_children(): w.destroy()
            self._rows.clear()

            self.inner_list=ctk.CTkScrollableFrame(self.list_box,fg_color="transparent",
                scrollbar_button_color=t["border"],
                scrollbar_button_hover_color=t["accent"])
            self.inner_list.pack(fill="both",expand=True,padx=4,pady=4)
            self.inner_list.grid_columnconfigure(0,weight=1)

            self.pl_lbl=ctk.CTkLabel(self.inner_list,text=f"{self._pl_title}  ·  0 videos",
                font=ctk.CTkFont(family=FF,size=14,weight="bold"),
                text_color=t["accent2"])
            self.pl_lbl.grid(row=0,column=0,sticky="w",padx=10,pady=(6,4))
            
        new_start = len(self._entries)
        self._entries.extend(resolved)
        self.pl_lbl.configure(text=f"{self._pl_title}  ·  {len(self._entries)} videos")

        for i,e in enumerate(resolved):
            idx = new_start + i
            r=VideoRow(self.inner_list,idx,e["title"],e["duration"],e["url"],self._upd_count,t)
            r.grid(row=idx+1,column=0,sticky="we",padx=4,pady=1)
            self._rows.append(r)

        self._upd_count(); self._upd_preview()
        
        if chunk_len >= 50:
            self.fetch_btn.configure(text="Waiting…")
            self._show_stationary_prompt()
        else:
            self.fetch_btn.configure(text="Fetch",state="normal")
            if self._entries:
                threading.Thread(target=self._fetch_first_info,args=(self._entries[0]["url"],),daemon=True).start()

    def _show_stationary_prompt(self):
        t = self._t
        if hasattr(self, '_stat_prompt') and self._stat_prompt.winfo_exists():
            self._stat_prompt.destroy()
            
        self._stat_prompt = ctk.CTkFrame(self.list_box, fg_color=t["surface2"], border_color=t["accent"], border_width=2, corner_radius=10)
        self._stat_prompt.place(relx=0.5, rely=0.96, anchor="s")
        
        ctk.CTkLabel(self._stat_prompt, text=f"{len(self._entries)} items fetched. Continue fetching?", font=ctk.CTkFont(family=FF, size=13, weight="bold"), text_color=t["text"]).pack(side="left", padx=(20, 10), pady=12)
        
        ctk.CTkButton(self._stat_prompt, text="Keep Top", width=90, height=28, corner_radius=8, fg_color=t["surface"], hover_color=t["border"], font=ctk.CTkFont(family=FF, size=12), text_color=t["text"], command=self._keep_top).pack(side="left", padx=(5, 5), pady=12)
        
        ctk.CTkButton(self._stat_prompt, text="Continue Fetch", width=110, height=28, corner_radius=8, fg_color=t["accent"], hover_color=t["accent_hover"], font=ctk.CTkFont(family=FF, size=12, weight="bold"), text_color=t["text"], command=self._continue_fetch).pack(side="left", padx=(5, 20), pady=12)

    def _keep_top(self):
        if hasattr(self, '_stat_prompt') and self._stat_prompt.winfo_exists():
            self._stat_prompt.destroy()
        self.fetch_btn.configure(text="Fetch", state="normal")
        if self._entries:
            threading.Thread(target=self._fetch_first_info,args=(self._entries[0]["url"],),daemon=True).start()

    def _continue_fetch(self):
        if hasattr(self, '_stat_prompt') and self._stat_prompt.winfo_exists():
            self._stat_prompt.destroy()
        self.fetch_btn.configure(text="Loading…", state="disabled")
        self._current_fetch_start += 50
        self._fetch_chunk()

    def _fetch_first_info(self, url):
        opts={"quiet":True,"no_warnings":True,"skip_download":True}
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                info=y.extract_info(url,download=False)
            f_aud = [f for f in info.get("formats",[]) if f.get("vcodec")=="none" and f.get("tbr")]
            f_vid = [f for f in info.get("formats",[]) if f.get("vcodec")!="none" and f.get("height")]
            abps = max([f.get("tbr",0) for f in f_aud] or [0])
            vres = max([f.get("height",0) for f in f_vid] or [0])
            txt = f"Original / Native Specs:\nAudio: ~{int(abps)} kbps\nVideo: {vres}p"
            
            thumb_url = info.get("thumbnail")
            ctk_im = None
            if thumb_url:
                req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as u:
                    raw_data = u.read()
                im = Image.open(io.BytesIO(raw_data))
                w, h = im.size
                ratio = 160 / max(w, h)
                im = im.resize((int(w*ratio), int(h*ratio)), Image.Resampling.LANCZOS)
                ctk_im = ctk.CTkImage(im, size=im.size)
            
            self.after(0, lambda: self._rows[0].set_hover_info(ctk_im, txt) if self._rows else None)
        except Exception:
            pass # ignore hover fetch errors

    # ── Build output path ────────────────────────────────────────────────────

    def _build_outtmpl(self, count, row_index=None):
        """Build the yt-dlp outtmpl string from user templates."""
        base=self.dest_var.get().strip() or os.path.join(os.getcwd(),"Downloads")
        parts=[base]

        def replace_vars(s, idx):
            if idx is not None:
                s = s.replace("{number}", str(idx+1))
                s = s.replace("{number2}", f"{idx+1:02d}")
                s = s.replace("{number3}", f"{idx+1:03d}")
            clean_pl = sanitize(self._pl_title).replace("%", "%%")
            s = s.replace("{playlist}", clean_pl)
            return tok_to_yt(s)

        if count>1:
            if self.use_pl_folder.get():
                pl_tmpl=self.pl_folder_var.get().strip() or DEFAULT_FOLDER_TMPL
                parts.append(replace_vars(pl_tmpl, row_index))
            if self.use_ep_folder.get():
                ep_tmpl=self.ep_folder_var.get().strip() or DEFAULT_EP_TMPL
                parts.append(replace_vars(ep_tmpl, row_index))

        file_tmpl=self.file_var.get().strip() or DEFAULT_FILE_TMPL
        parts.append(replace_vars(file_tmpl, row_index)+".%(ext)s")

        return os.path.join(*parts)

    # ── Download ─────────────────────────────────────────────────────────────

    def _on_stop(self):
        if self._downloading:
            self._cancel_download = True
            self.stop_btn.configure(text="Stopping…", state="disabled")

    def _on_download(self):
        if self._downloading: return
        sel=[r for r in self._rows if r.selected.get()]
        if not sel:
            self._show_overlay("Nothing selected","Select at least one video.", False)
            return
        self._downloading=True
        self._cancel_download=False
        self.dl_btn.configure(text="Downloading…",state="disabled")
        self.stop_btn.configure(text="Stop", state="normal")
        self.stop_btn.pack(side="right", padx=(0, 10))
        self.progress.set(0)
        self.pct_lbl.configure(text="0%")
        threading.Thread(target=self._dl_w,args=(sel,),daemon=True).start()

    def _dl_w(self,rows):
        t=self._t
        fmt=self.fmt_var.get().upper()
        bitrate=str(bps(self.bps_var.get()))
        res=RES_V.get(self.res_var.get(),"1080p")
        fps=FR_V.get(self.fps_var.get(),"30")
        total=len(rows)

        for idx,row in enumerate(rows):
            if getattr(self, "_cancel_download", False):
                break
            
            outtmpl=self._build_outtmpl(total, row.original_index)
            # Ensure base dirs exist
            out_dir=os.path.dirname(outtmpl.split("%(")[0])
            if out_dir:
                os.makedirs(out_dir,exist_ok=True)

            name=row.title_text
            self.after(0,lambda n=name,i=idx: (
                self.dl_status_lbl.configure(text=f"Downloading: {n}  ({i+1}/{total})"),
                self.pct_lbl.configure(text=f"{int(i/total*100)}%")
            ))
            self.after(0,lambda r=row: r.set_status("downloading…",t["accent2"]))

            # Build yt-dlp options
            pp=[]
            if is_audio(fmt):
                codec=AUDIO_CODEC.get(fmt,"mp3")
                ydl_opts={
                    "format":"bestaudio/best",
                    "outtmpl":outtmpl,
                    "quiet":True,"no_warnings":True,
                }
                pp_opt = {"key":"FFmpegExtractAudio", "preferredcodec":codec}
                if bitrate != "-1":
                    pp_opt["preferredquality"] = bitrate
                pp.append(pp_opt)
            else:
                ext=VID_EXT.get(fmt,"mp4")
                if res == "Original" or fps == "Original":
                    format_str = f"bestvideo[ext={ext}]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                else:
                    h=res.replace("p","")
                    format_str = (f"bestvideo[height<={h}][fps<={fps}][ext={ext}]+bestaudio[ext=m4a]/"
                                  f"bestvideo[height<={h}][fps<={fps}]+bestaudio/"
                                  f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best")
                ydl_opts={
                    "format": format_str,
                    "outtmpl":outtmpl,"merge_output_format":ext,
                    "quiet":True,"no_warnings":True,
                }
            if self.use_ep_folder.get():
                ydl_opts["writesubtitles"] = True
                ydl_opts["writeautomaticsub"] = True

            # Thumbnail options
            if self.dl_thumb_var.get():
                ydl_opts["writethumbnail"]=True
            if self.embed_thumb_var.get():
                pp.append({"key":"EmbedThumbnail"})
                # AtomicParsley or mutagen needed for embedding
                ydl_opts["writethumbnail"]=True

            last_filename = [None]
            def progress_hook(d):
                if getattr(self, "_cancel_download", False):
                    raise Exception("Cancelled by user")
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '')
                    if p:
                        p = re.sub(r'\x1b[^m]*m', '', p).strip()
                        self.after(0, lambda r=row, p_str=p: r.set_status(f"downloading… {p_str}", t["accent2"]))
                elif d['status'] == 'finished':
                    if d.get('info_dict', {}).get('_filename'):
                        last_filename[0] = d.get('info_dict')['_filename']
                    elif d.get('filename'):
                        last_filename[0] = d.get('filename')

            if pp:
                ydl_opts["postprocessors"]=pp

            ydl_opts["progress_hooks"] = [progress_hook]

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as y:
                    y.download([row.url])
                
                if self.use_ep_folder.get() and last_filename[0] and not getattr(self, "_cancel_download", False):
                    base_no_ext = os.path.splitext(last_filename[0])[0]
                    subs = glob.glob(base_no_ext + '.*.vtt') + glob.glob(base_no_ext + '.*.srt') + glob.glob(base_no_ext + '.*.lrc') + glob.glob(base_no_ext + '.*.ass') + glob.glob(base_no_ext + '.*.ttml')
                    if not subs:
                        typ = "lyrics" if is_audio(fmt) else "subtitles"
                        self.after(0, lambda r=row.title_text, ty=typ: self._show_overlay(f"No {ty} found", f"Could not find {ty} for:\n{r}", True))
                
                self.after(0,lambda r=row: r.set_status("✓ done",t["success"]))
            except Exception as e:
                err_str = str(e).lower()
                short = "✗ Error"
                if "sign in to confirm your age" in err_str or "age-restricted" in err_str:
                    short = "✗ Age-Restricted"
                elif "private video" in err_str:
                    short = "✗ Private Video"
                elif "unavailable" in err_str:
                    short = "✗ Unavailable"
                elif "geo-blocked" in err_str or "country" in err_str:
                    short = "✗ Region-Blocked"
                elif "requested format is not available" in err_str:
                    short = "✗ Format Unavailable"
                if "cancelled by user" in err_str:
                    self.after(0, lambda r=row: r.set_status("✗ Cancelled", t["warning"]))
                    break # exit the loop if cancelled by user
                else:
                    self.after(0,lambda r=row,m=short: r.set_status(m,t["error"]))

            if not getattr(self, "_cancel_download", False):
                pct=int((idx+1)/total*100)
                self.after(0,lambda v=(idx+1)/total,p=pct: (
                    self.progress.set(v), self.pct_lbl.configure(text=f"{p}%")))

        self.after(0,self._dl_done)

    def _dl_done(self):
        self._downloading=False
        self.dl_btn.configure(text="Download Selected",state="normal")
        self.stop_btn.pack_forget()
        
        if getattr(self, "_cancel_download", False):
            self.dl_status_lbl.configure(text="Download stopped")
            self._show_overlay("Stopped","Download stopped by user.", False)
        else:
            self.dl_status_lbl.configure(text="Done!")
            self.pct_lbl.configure(text="100%")
            self._show_overlay("Done","All downloads completed.", False)


# ═══════════════════════════════════════════════════════════════════════════════
if __name__=="__main__":
    App().mainloop()
