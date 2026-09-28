"""Módulo de Pós-Processamento Fotográfico.

Mantém os pixels originais limpos, preservando a nitidez da foto real do cliente
sem adicionar granulação artificial ou ruído que destaque artefatos de IA.
"""
from __future__ import annotations


def aplicar_pos_processamento_fotografico(imagem_bytes: bytes) -> bytes:
    """Retorna os bytes originais da imagem com máxima nitidez e sem granulação artificial."""
    return imagem_bytes
