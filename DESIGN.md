---
version: alpha
name: UEFS Financeiro Clean Corporate
colors:
  primary: "#00664F"      # Verde Esmeralda Institucional da UEFS
  primary-hover: "#004D3C"
  secondary: "#0f2b46"    # Azul Marinho Profundo
  neutral-bg: "#f8fafc"   # Fundo Cinza Claro Slate
  neutral-surface: "#ffffff"
  neutral-border: "#cbd5e1"
  text-primary: "#0f172a"
  text-secondary: "#475569"
  error: "#ef4444"
typography:
  headline:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "24px"
    fontWeight: "700"
    lineHeight: "1.2"
  body-md:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "1.5"
  label-sm:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "12px"
    fontWeight: "600"
    lineHeight: "1.0"
rounded:
  sm: "4px"
  md: "6px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral-surface}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
  card-base:
    backgroundColor: "{colors.neutral-surface}"
    rounded: "{rounded.md}"
    padding: "24px"
---

# UEFS Financeiro Design System

## Overview
Este é o guia de design system e tokens para o **Sistema de Cálculo de Impacto Financeiro da UEFS**.
O objetivo visual é transmitir **confiança**, **estabilidade**, e **precisão matemática**.
A interface adota uma estética limpa, corporativa e com alta legibilidade.

## Colors
- **Primary (#00664F)**: Verde esmeralda que representa a identidade institucional da universidade (UEFS) e guia as ações principais do usuário.
- **Secondary (#0f2b46)**: Azul marinho profissional utilizado para contrastar e definir estruturas (ex: cabeçalhos secundários, destaques).
- **Neutral Background (#f8fafc)**: Base limpa de baixa carga cognitiva.
- **Neutral Surface (#ffffff)**: Fundo de cartões, tabelas e modais para foco e legibilidade de dados numéricos.

## Shapes
- **Geometria Corporativa Afiada**: Evita arredondamento excessivo do padrão de consumo moderno. Os botões utilizam `rounded: 4px` e os cards `rounded: 6px` para transmitir seriedade e rigor técnico.

## Do's and Don'ts
- **Do**: Usar o verde esmeralda apenas para interações primárias (botões principais, links ativos).
- **Do**: Garantir alto contraste (mínimo de 4.5:1) nas tabelas e formulários.
- **Don't**: Utilizar degradês coloridos ou o tom de roxo (AI-purple) no layout.
- **Don't**: Exceder 6px de `border-radius` em tabelas ou caixas de entrada de dados.
