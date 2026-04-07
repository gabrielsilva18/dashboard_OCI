import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


LISTA_PROCED_ESPECIALIDADE = {
    # Cardiologia
    "0902010018": "Cardiologia",
    "0902010026": "Cardiologia",
    "0902010034": "Cardiologia",
    "0902010042": "Cardiologia",
    "0902010050": "Cardiologia",
    "0902010069": "Cardiologia",

    # Ortopedia
    "0903010011": "Ortopedia",
    "0903010020": "Ortopedia",
    "0903010038": "Ortopedia",
    "0903010046": "Ortopedia",

    # Oftalmologia
    "0905010019": "Oftalmologia",
    "0905010027": "Oftalmologia",
    "0905010035": "Oftalmologia",
    "0905010043": "Oftalmologia",
    "0905010051": "Oftalmologia",
    "0905010060": "Oftalmologia",
    "0905010078": "Oftalmologia",

    # Otorrino
    "0904010015": "Otorrino",
    "0904010023": "Otorrino",
    "0904010031": "Otorrino",

    # Oncologia
    "0901010014": "Oncologia",
    "0901010090": "Oncologia",
    "0901010103": "Oncologia",
    "0901010057": "Oncologia",
    "0901010111": "Oncologia",
    "0901010120": "Oncologia",
    "0901010049": "Oncologia",
    "0901010073": "Oncologia",
    "0901010081": "Oncologia",

    # Ginecologia
    "0906010012": "Ginecologia",
    "0906010020": "Ginecologia",
    "0906010039": "Ginecologia",
    "0906010047": "Ginecologia",
    "0906010055": "Ginecologia",
}


def code10_to_hyphen(code10: str) -> str:
    """
    O arquivo costuma vir como: 9 digitos + '-' + 1 digito (ex: 090501003-5).
    A sua lista veio como: 10 digitos (ex: 0905010035).
    """

    code10 = code10.strip()
    if len(code10) != 10 or not code10.isdigit():
        raise ValueError(f"Codigo esperado com 10 digitos: {code10!r}")
    return f"{code10[:-1]}-{code10[-1]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="RHOSPIAPAC.txt")
    parser.add_argument("--out", default="dashboard.html")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)

    if not input_path.exists():
        raise SystemExit(f"Arquivo nao encontrado: {input_path}")

    # Mapa para converter o codigo encontrado no texto (com '-') para a especialidade
    special_by_code_hyphen = {}
    for code10, esp in LISTA_PROCED_ESPECIALIDADE.items():
        special_by_code_hyphen[code10_to_hyphen(code10)] = esp

    # Contagem por especialidade e por codigo (na forma 10 digitos)
    counts_by_specialty = Counter()
    counts_by_code10 = Counter()

    # O texto tende a conter codigos como: 090501003-5
    # \b pode funcionar razoavelmente como fronteira entre digito e '-'
    code_re = re.compile(r"\b\d{9}-\d\b")

    with input_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Conta 1 ocorrencia por match (evita supercontagem caso o mesmo codigo apareca
            # mais de uma vez na mesma linha).
            for m in code_re.finditer(line):
                code = m.group(0)
                esp = special_by_code_hyphen.get(code)
                if not esp:
                    continue

                counts_by_specialty[esp] += 1
                # Converter de volta para o formato 10 digitos (sem '-')
                code10 = code.replace("-", "")
                counts_by_code10[code10] += 1

    total_geral = sum(counts_by_specialty.values())

    # Garantir que aparecerao especialidades mesmo com 0
    all_specialties = sorted(set(LISTA_PROCED_ESPECIALIDADE.values()))
    specialty_rows = []
    for esp in all_specialties:
        specialty_rows.append(
            {"especialidade": esp, "total": int(counts_by_specialty.get(esp, 0))}
        )

    # Linhas por codigo (tambem com 0, na ordem original)
    code_rows = []
    # Preservar a ordem "agrupada" conforme a lista do colega
    for code10, esp in LISTA_PROCED_ESPECIALIDADE.items():
        code_rows.append(
            {
                "procedimento": code10,
                "especialidade": esp,
                "total": int(counts_by_code10.get(code10, 0)),
            }
        )

    payload = {
        "total_geral": int(total_geral),
        "por_especialidade": specialty_rows,
        "por_codigo": code_rows,
        "fonte": str(input_path),
    }

    html = f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard - Contagem por Especialidade</title>
  <style>
    :root {{
      --bg: #0b1020;
      --card: #111a33;
      --text: #e9eefc;
      --muted: #a9b4d6;
      --accent: #58a6ff;
      --accent2: #34d399;
      --danger: #f87171;
      --border: rgba(233, 238, 252, 0.12);
    }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Helvetica Neue", sans-serif;
      background: radial-gradient(1200px 800px at 10% 0%, rgba(88, 166, 255, 0.18), transparent 55%),
                  radial-gradient(1000px 700px at 90% 10%, rgba(52, 211, 153, 0.14), transparent 60%),
                  var(--bg);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 28px 18px 42px;
    }}
    .hero {{
      display: flex;
      gap: 14px;
      align-items: baseline;
      justify-content: space-between;
      flex-wrap: wrap;
      border: 1px solid var(--border);
      background: rgba(17, 26, 51, 0.6);
      padding: 18px 18px;
      border-radius: 16px;
      backdrop-filter: blur(6px);
    }}
    h1 {{
      margin: 0;
      font-size: 18px;
      letter-spacing: 0.2px;
      font-weight: 700;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
    }}
    .grid {{
      margin-top: 16px;
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16px;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      border: 1px solid var(--border);
      background: rgba(17, 26, 51, 0.55);
      border-radius: 16px;
      padding: 14px 14px;
    }}
    .card h2 {{
      margin: 0 0 10px;
      font-size: 14px;
      color: var(--muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.9px;
    }}
    .total {{
      font-size: 34px;
      font-weight: 800;
      margin: 6px 0 0;
    }}
    .hint {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }}

    .bars {{
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }}
    .barrow {{
      display: grid;
      grid-template-columns: 180px 1fr 70px;
      gap: 10px;
      align-items: center;
    }}
    @media (max-width: 520px) {{
      .barrow {{ grid-template-columns: 1fr; }}
    }}
    .label {{
      color: var(--text);
      font-weight: 700;
      font-size: 13px;
    }}
    .track {{
      height: 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.18);
      overflow: hidden;
    }}
    .fill {{
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      border-radius: 999px;
      transition: width 700ms ease;
    }}
    .val {{
      text-align: right;
      font-weight: 800;
      color: var(--text);
      font-size: 13px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 8px;
    }}
    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{
      text-align: left;
      color: var(--muted);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      font-size: 12px;
    }}
    td {{
      color: var(--text);
    }}
    .smallmuted {{
      color: var(--muted);
      font-size: 12px;
    }}
    .pill {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.16);
      color: var(--muted);
      font-weight: 800;
      font-size: 12px;
      white-space: nowrap;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div>
        <h1>Dashboard - Contagem por Especialidade</h1>
        <div class="meta">Fonte: <span class="pill">{payload["fonte"]}</span></div>
      </div>
      <div class="meta">Total geral de ocorrencias: <b>{payload["total_geral"]}</b></div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>Totais por Especialidade</h2>
        <div class="bars" id="bars"></div>
      </div>

      <div class="card">
        <h2>Totais por Codigo (apenas os da lista)</h2>
        <div class="smallmuted">Mostrando todos os codigos da lista (inclusive os que deram 0).</div>
        <table>
          <thead>
            <tr>
              <th>Procedimento</th>
              <th>Especialidade</th>
              <th style="text-align:right;">Total</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    const data = {json.dumps(payload)};
    const max = Math.max(...data.por_especialidade.map(x => x.total), 0);
    const bars = document.getElementById('bars');
    const rows = document.getElementById('rows');

    for (const item of data.por_especialidade) {{
      const pct = max === 0 ? 0 : (item.total / max) * 100;
      const el = document.createElement('div');
      el.className = 'barrow';
      el.innerHTML = `
        <div class="label">${{item.especialidade}}</div>
        <div class="track"><div class="fill" style="width:${{pct}}%"></div></div>
        <div class="val">${{item.total}}</div>
      `;
      bars.appendChild(el);
    }}

    for (const item of data.por_codigo) {{
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><b>${{item.procedimento}}</b></td>
        <td>${{item.especialidade}}</td>
        <td style="text-align:right; font-weight:800;">${{item.total}}</td>
      `;
      rows.appendChild(tr);
    }}
  </script>
</body>
</html>
"""

    out_path.write_text(html, encoding="utf-8")

    # Log rapido no terminal
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nDashboard gerado em: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

