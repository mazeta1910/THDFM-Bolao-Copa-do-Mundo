from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Jogo:
    id: int
    data: str
    casa: str
    fora: str
    gols_casa: int | None = None
    gols_fora: int | None = None

    @property
    def realizado(self) -> bool:
        return self.gols_casa is not None and self.gols_fora is not None


@dataclass
class Palpite:
    participante: str
    jogo_id: int
    palpite_casa: int
    palpite_fora: int


@dataclass
class PontosJogo:
    placar: int = 0
    vencedor: int = 0
    gols_casa: int = 0
    gols_fora: int = 0

    @property
    def total(self) -> int:
        return self.placar + self.vencedor + self.gols_casa + self.gols_fora


@dataclass
class PontosParticipante:
    participante: str
    placar: int = 0
    vencedor: int = 0
    gols_casa: int = 0
    gols_fora: int = 0

    @property
    def soma(self) -> int:
        return self.placar + self.vencedor + self.gols_casa + self.gols_fora

    def adicionar(self, pontos: PontosJogo) -> None:
        self.placar += pontos.placar
        self.vencedor += pontos.vencedor
        self.gols_casa += pontos.gols_casa
        self.gols_fora += pontos.gols_fora


@dataclass
class ClassificacaoLinha:
    posicao: int
    participante: str
    placar: int
    vencedor: int
    gols_casa: int
    gols_fora: int
    soma: int


@dataclass
class BolaoData:
    jogos: list[Jogo] = field(default_factory=list)
    palpites: list[Palpite] = field(default_factory=list)
    participantes: list[str] = field(default_factory=list)
