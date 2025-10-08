#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tienda Aurelion - Consultor de Documentación (CLI)
-----------------------------------------------
- Funciones:
  1) Listar documentos detectados (.md y .png)
  2) Ver índice (TOC) por encabezados de un .md
  3) Leer un documento con paginación
  4) Buscar texto en todos los .md (muestra coincidencias con contexto)
  5) Ver resumen de sugerencias (si existe 4.Sugerencias_Copilot.md)
  0) Salir
"""

import os
import sys
import re
import textwrap
from shutil import get_terminal_size
from typing import List, Dict, Tuple

MD_EXT = {".md", ".markdown"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg"}


def ask_int(prompt: str, valid: List[int]) -> int:
    """Pide un entero del conjunto válido."""
    while True:
        val = input(prompt).strip()
        if val.isdigit() and int(val) in valid:
            return int(val)
        print(f"Opción inválida. Opciones válidas: {valid}")


def clear():
    """Limpia pantalla si es posible."""
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass


def read_text(path: str) -> str:
    """Lee archivo de texto en UTF-8 con fallback."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def list_files(root: str) -> Tuple[List[str], List[str]]:
    """Devuelve listas (mds, imgs) en la carpeta."""
    mds, imgs = [], []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in MD_EXT:
            mds.append(p)
        elif ext in IMG_EXT:
            imgs.append(p)
    return mds, imgs


def build_toc(md_text: str) -> List[Tuple[int, str, int]]:
    """
    Extrae TOC de encabezados Markdown.
    Retorna lista de tuplas (nivel, texto, línea).
    """
    toc = []
    for i, line in enumerate(md_text.splitlines(), start=1):
        m = re.match(r"^(#{1,6})\s+(.*)", line.strip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            toc.append((level, title, i))
    return toc


def paginate(text: str, title: str = "", width: int = 0, height: int = 0):
    """Muestra texto paginado según tamaño de terminal."""
    if width <= 0 or height <= 0:
        cols, rows = get_terminal_size(fallback=(100, 30))
    else:
        cols, rows = width, height

    # Reservamos 3 líneas para encabezado/ayuda
    rows = max(10, rows - 3)
    lines = []
    for raw_line in text.splitlines():
        wrapped = textwrap.wrap(raw_line, width=cols) or [""]
        lines.extend(wrapped)

    total = len(lines)
    idx = 0
    while idx < total:
        clear()
        if title:
            print(f"{title}\n" + "-" * (len(title) + 2))
        end = min(idx + rows, total)
        for i in range(idx, end):
            print(lines[i])
        idx = end
        if idx < total:
            input("\n⏎ Enter para continuar, Ctrl+C para salir…")


def search_all(md_paths: List[str], query: str, context: int = 1) -> List[Tuple[str, int, str]]:
    """Busca en todos los .md y retorna (archivo, linea, fragmento)."""
    query_low = query.lower()
    results: List[Tuple[str, int, str]] = []
    for p in md_paths:
        text = read_text(p)
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if query_low in line.lower():
                # Tomar contexto
                start = max(1, i - context)
                end = min(len(lines), i + context)
                snippet = "\n".join(lines[start-1:end])
                # Resaltar simple
                snippet = re.sub(
                    re.escape(query), lambda m: f"[{m.group(0)}]", snippet, flags=re.IGNORECASE
                )
                results.append((p, i, snippet))
    return results


def pick_from_list(items: List[str], title: str) -> int:
    """Muestra lista numerada y devuelve índice elegido (o -1 si vacío)."""
    if not items:
        print("No hay elementos disponibles.")
        return -1
    print(title)
    for i, p in enumerate(items, start=1):
        print(f"  {i}) {os.path.basename(p)}")
    return ask_int("Elija número: ", list(range(1, len(items) + 1))) - 1


def show_toc(md_path: str):
    """Muestra TOC de un .md con líneas destino."""
    text = read_text(md_path)
    toc = build_toc(text)
    print(f"\n📚 Índice de {os.path.basename(md_path)}")
    if not toc:
        print("  (No se detectaron encabezados Markdown)")
        return
    for level, title, line in toc:
        indent = "  " * (level - 1)
        print(f"{indent}- L{line}: {title}")


def open_doc_paged(md_path: str):
    """Abre documento paginado."""
    text = read_text(md_path)
    paginate(text, title=os.path.basename(md_path))


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    if not os.path.isdir(root):
        print(f"Carpeta no válida: {root}")
        sys.exit(1)

    while True:
        clear()
        print("===== TIENDA AURELION - CONSULTOR DE DOCUMENTACIÓN =====")
        print(f"Carpeta: {root}\n")
        print("1) Listar documentos")
        print("2) Ver índice (TOC) de un .md")
        print("3) Leer un .md con paginación")
        print("4) Buscar texto en todos los .md")
        print("5) Resumen de sugerencias")
        print("0) Salir")

        op = ask_int("\nElija opción: ", [0, 1, 2, 3, 4, 5])

        # Cargar inventario cada vuelta (por si agregaste/quitas archivos)
        md_paths, img_paths = list_files(root)

        if op == 0:
            print("Aduiós.")
            break

        elif op == 1:
            clear()
            print("📂 Documentos detectados:\n")
            if md_paths:
                print("Markdown:")
                for p in md_paths:
                    print("  -", os.path.basename(p))
            else:
                print("No se hallaron archivos .md")

            if img_paths:
                print("\nImágenes:")
                for p in img_paths:
                    print("  -", os.path.basename(p), "→", p)
            else:
                print("\nNo se hallaron imágenes (PNG/JPG/SVG)")
            input("\n⏎ Enter para continuar…")

        elif op == 2:
            clear()
            idx = pick_from_list(md_paths, "Elija documento para ver su índice:")
            if idx >= 0:
                clear()
                show_toc(md_paths[idx])
            input("\n⏎ Enter para continuar…")

        elif op == 3:
            clear()
            idx = pick_from_list(md_paths, "Elija documento para leer:")
            if idx >= 0:
                open_doc_paged(md_paths[idx])

        elif op == 4:
            clear()
            if not md_paths:
                print("No hay .md para buscar.")
                input("\n⏎ Enter para continuar…")
                continue
            q = input("Texto a buscar (mín. 2 caracteres): ").strip()
            if len(q) < 2:
                print("Consulta demasiado corta.")
                input("\n⏎ Enter para continuar…")
                continue
            results = search_all(md_paths, q, context=1)
            clear()
            print(f"Resultados para '{q}': {len(results)}\n")
            for p, line, snip in results[:200]:  # límite de seguridad
                print(f"— {os.path.basename(p)} (línea {line})")
                print(textwrap.indent(snip, prefix="  "))
                print("-" * 60)
            if not results:
                print("Sin coincidencias.")
            input("\n⏎ Enter para continuar…")

        elif op == 5:
            clear()
            # Abrimos si existe el archivo con ese nombre o similar
            cand = [p for p in md_paths if os.path.basename(p).lower().startswith("4.sugerencias")]
            if not cand:
                print("No se encontró el archivo de sugerencias (ej. 4.Sugerencias_Copilot.md).")
            else:
                open_doc_paged(cand[0])

        else:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
