"""
Manejo Inteligente de Bois - Modulo 5
Snippet que implementa o Diagrama de Componentes (DC) e o Diagrama de Implantacao (DI).

  Parte 1  Dominio (o mesmo piquete do modulo 4)
  Parte 2  Interfaces: as "bolinhas" (fornecidas) e "soquetes" (requeridas) do DC
  Parte 3  Componentes, separados por DDD: core, support, generic e infraestrutura
  Parte 4  Montagem: os conectores do DC, conferidos automaticamente
  Parte 5  Implantacao: nos, artefatos e conexoes do DI, conferidos contra o DC
  Parte 6  Simulacao

Os servicos externos (satelite, clima e Gemini) sao simulados: roda sem internet e sem chave.
Ementa do modulo 5 no codigo:
  - Gestao de riscos: R3 (validador da IA), R6 (nuvem no satelite), R7 (cota gratuita).
  - Gestao de aquisicoes: cada servico comprado fica atras de um adaptador (AQ-01 a AQ-06).
  - Software de gestao: cada componente aponta para os cartoes do Trello / atividades do Gantt.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Protocol


# ======================================================================
# PARTE 1 - DOMINIO
# ======================================================================

CATEGORIAS = ("bois", "vacas", "bezerros")


@dataclass
class Piquete:
    id: int
    nome: str
    poligono: list[tuple[float, float]]
    area_m2: float
    animais: dict[str, int] = field(default_factory=lambda: dict.fromkeys(CATEGORIAS, 0))

    @property
    def lotacao(self) -> int:
        return sum(self.animais.values())

    @property
    def centroide(self) -> tuple[float, float]:
        xs, ys = zip(*self.poligono)
        return sum(xs) / len(xs), sum(ys) / len(ys)


@dataclass(frozen=True)
class LeituraNDVI:
    ndvi: float
    nuvem: float  # fracao da imagem coberta por nuvem, de 0 a 1
    data: date


@dataclass(frozen=True)
class Previsao:
    chuva_7d_mm: float
    consultado_em: datetime


@dataclass(frozen=True)
class Recomendacao:
    piquete_id: int
    acao: str  # RETIRAR, MANTER, PODE_RECEBER, DESCANSAR ou SEM_DADOS
    texto: str
    origem: str  # "gemini" ou "regra" (quando a IA e barrada ou a cota acabou)
    data: date


class AcessoNegado(Exception):
    """Equivale ao HTTP 401 do criterio de qualidade 4.2."""


class CotaEsgotada(Exception):
    """Risco R7: a cota gratuita do servico acabou."""


# ======================================================================
# PARTE 2 - INTERFACES
# Cada Protocol e uma interface do DC. Um componente FORNECE uma interface
# quando a implementa e REQUER uma interface quando a recebe no construtor.
# ======================================================================

class IRepositorio(Protocol):
    def salvar_piquete(self, piquete: Piquete) -> None: ...
    def buscar_piquete(self, piquete_id: int) -> Piquete: ...
    def listar_piquetes(self) -> list[Piquete]: ...
    def salvar_leitura(self, piquete_id: int, leitura: LeituraNDVI) -> None: ...
    def ultima_leitura(self, piquete_id: int) -> LeituraNDVI | None: ...
    def salvar_recomendacao(self, rec: Recomendacao) -> None: ...
    def historico(self, piquete_id: int) -> list[Recomendacao]: ...
    def buscar_usuario(self, email: str) -> dict | None: ...
    def salvar_usuario(self, email: str, dados: dict) -> None: ...


class ISatelite(Protocol):
    def obter_ndvi(self, poligono: list[tuple[float, float]], data: date) -> LeituraNDVI: ...


class IClima(Protocol):
    def previsao(self, ponto: tuple[float, float]) -> Previsao: ...


class ILLM(Protocol):
    def gerar_texto(self, prompt: str) -> str: ...


class IAutenticacao(Protocol):
    def login(self, email: str, senha: str) -> str: ...
    def validar(self, token: str) -> str: ...


class ICadastro(Protocol):
    def cadastrar_piquete(self, nome: str, poligono: list[tuple[float, float]], area_m2: float) -> int: ...
    def buscar(self, piquete_id: int) -> Piquete: ...
    def listar(self) -> list[Piquete]: ...


class IOcupacao(Protocol):
    def movimentar(self, tipo: str, origem: int | None, destino: int | None, quantidades: dict[str, int]) -> None: ...


class IMonitoramento(Protocol):
    def atualizar_ndvi(self, piquete_id: int, hoje: date) -> LeituraNDVI | None: ...
    def leitura_valida(self, piquete_id: int, hoje: date) -> LeituraNDVI | None: ...


class IRecomendacao(Protocol):
    def recomendar(self, piquete_id: int, hoje: date) -> Recomendacao: ...


class IDashboard(Protocol):
    def consultar(self) -> list[dict]: ...


# ======================================================================
# PARTE 3 - COMPONENTES
# Cada classe declara a sua posicao no DC: camada DDD, pacote da EAP,
# interfaces fornecidas e requeridas, e as atividades do Gantt / cartoes do Trello.
# ======================================================================

# ---------------- INFRAESTRUTURA (adaptadores para banco e servicos comprados) ----------------

class RepositorioPostgres:
    """Na implantacao conversa com o PostgreSQL; aqui guarda em memoria."""
    CAMADA, EAP, GANTT = "infra", "-", (2, 9)
    FORNECE, REQUER = ("IRepositorio",), ()
    NO_EXTERNO = "Servidor de Banco"

    def __init__(self) -> None:
        self._piquetes: dict[int, Piquete] = {}
        self._leituras: dict[int, list[LeituraNDVI]] = {}
        self._recomendacoes: dict[int, list[Recomendacao]] = {}
        self._usuarios: dict[str, dict] = {}

    def salvar_piquete(self, piquete: Piquete) -> None:
        self._piquetes[piquete.id] = piquete

    def buscar_piquete(self, piquete_id: int) -> Piquete:
        if piquete_id not in self._piquetes:
            raise KeyError(f"Piquete {piquete_id} nao existe.")
        return self._piquetes[piquete_id]

    def listar_piquetes(self) -> list[Piquete]:
        return list(self._piquetes.values())

    def salvar_leitura(self, piquete_id: int, leitura: LeituraNDVI) -> None:
        self._leituras.setdefault(piquete_id, []).append(leitura)

    def ultima_leitura(self, piquete_id: int) -> LeituraNDVI | None:
        leituras = self._leituras.get(piquete_id)
        return max(leituras, key=lambda l: l.data) if leituras else None

    def salvar_recomendacao(self, rec: Recomendacao) -> None:
        self._recomendacoes.setdefault(rec.piquete_id, []).append(rec)

    def historico(self, piquete_id: int) -> list[Recomendacao]:
        return list(self._recomendacoes.get(piquete_id, []))

    def buscar_usuario(self, email: str) -> dict | None:
        return self._usuarios.get(email)

    def salvar_usuario(self, email: str, dados: dict) -> None:
        self._usuarios[email] = dados


class AdaptadorSentinel:
    """AQ-01 - Imagens de satelite / NDVI. Comprar (usar gratuito no MVP)."""
    CAMADA, EAP, GANTT = "infra", "2.2", (5,)
    FORNECE, REQUER = ("ISatelite",), ()
    NO_EXTERNO = "Google Earth Engine"
    AQUISICAO = ("AQ-01", "Copernicus Sentinel-2 via Earth Engine", "uso nao comercial gratuito")

    def __init__(self, cenas: dict[tuple[float, float], list[LeituraNDVI]]) -> None:
        self._cenas = cenas  # simulacao: imagens por centroide, em ordem de data

    def obter_ndvi(self, poligono: list[tuple[float, float]], data: date) -> LeituraNDVI:
        xs, ys = zip(*poligono)
        chave = (sum(xs) / len(xs), sum(ys) / len(ys))
        cenas = [c for c in self._cenas.get(chave, []) if c.data <= data]
        if not cenas:
            raise LookupError("Nenhuma imagem para o periodo.")
        return cenas[-1]


class AdaptadorOpenMeteo:
    """AQ-03 - API de previsao do tempo (EAP 1.2). Comprar (plano gratuito no MVP)."""
    CAMADA, EAP, GANTT = "infra", "1.2", (6,)
    FORNECE, REQUER = ("IClima",), ()
    NO_EXTERNO = "Open-Meteo"
    AQUISICAO = ("AQ-03", "Open-Meteo", "plano gratuito")

    def previsao(self, ponto: tuple[float, float]) -> Previsao:
        return Previsao(chuva_7d_mm=12.0, consultado_em=datetime.now())


class ControleDeCota:
    """Risco R7: alerta quando o uso passa de 80% da cota e bloqueia em 100%."""

    def __init__(self, limite: int) -> None:
        self.limite, self.usado = limite, 0

    def consumir(self) -> None:
        if self.usado >= self.limite:
            raise CotaEsgotada(f"Cota de {self.limite} chamadas esgotada.")
        self.usado += 1
        if self.usado / self.limite > 0.8:
            print(f"    [R7] Alerta: {self.usado}/{self.limite} chamadas da cota gratuita usadas.")


class AdaptadorGemini:
    """AQ-02 - Modelo de linguagem para o texto da recomendacao. Comprar (cota gratuita)."""
    CAMADA, EAP, GANTT = "infra", "1.1", (7,)
    FORNECE, REQUER = ("ILLM",), ()
    NO_EXTERNO = "Google Gemini API"
    AQUISICAO = ("AQ-02", "Google Gemini", "cota gratuita")

    def __init__(self, cota: ControleDeCota) -> None:
        self._cota = cota

    def gerar_texto(self, prompt: str) -> str:
        self._cota.consumir()
        # Simulacao: o modelo responde sempre a mesma coisa, sem olhar os dados.
        # E exatamente o tipo de erro que o validador do risco R3 precisa barrar.
        return "MANTER o lote. Pastagem em boas condicoes, monitorar a lotacao."


# ---------------- SUPPORT ----------------

class Cadastros:
    """EAP 3 - Cadastro de piquete, bois e vegetacao."""
    CAMADA, EAP, GANTT = "support", "3", (2,)
    FORNECE, REQUER = ("ICadastro",), ("IRepositorio",)

    def __init__(self, repo: IRepositorio) -> None:
        self._repo = repo
        self._proximo_id = 1

    def cadastrar_piquete(self, nome: str, poligono: list[tuple[float, float]], area_m2: float) -> int:
        if len(poligono) < 3 or area_m2 <= 0:
            raise ValueError("Poligono precisa de 3 pontos e area maior que zero.")
        piquete = Piquete(self._proximo_id, nome, poligono, area_m2)
        self._repo.salvar_piquete(piquete)
        self._proximo_id += 1
        return piquete.id

    def buscar(self, piquete_id: int) -> Piquete:
        return self._repo.buscar_piquete(piquete_id)

    def listar(self) -> list[Piquete]:
        return self._repo.listar_piquetes()


class Monitoramento:
    """EAP 2 - Monitoramento de area, NDVI e estimativa de ocupacao."""
    CAMADA, EAP, GANTT = "support", "2", (4, 5)
    FORNECE, REQUER = ("IMonitoramento", "IOcupacao"), ("ISatelite", "IRepositorio")

    NUVEM_MAXIMA = 0.30    # risco R6: acima disso a imagem e descartada
    VALIDADE_DIAS = 7      # criterio de qualidade 1.1.1

    def __init__(self, satelite: ISatelite, repo: IRepositorio) -> None:
        self._satelite, self._repo = satelite, repo

    # ---- IOcupacao ----
    def movimentar(self, tipo: str, origem: int | None, destino: int | None,
                   quantidades: dict[str, int]) -> None:
        for categoria, qtd in quantidades.items():
            if categoria not in CATEGORIAS or not isinstance(qtd, int) or qtd < 0:
                raise ValueError(f"Quantidade invalida: {categoria}={qtd}")
        if tipo not in ("adicionar", "remover", "mover"):
            raise ValueError("Tipo de movimentacao invalido.")
        if tipo in ("remover", "mover"):
            p_origem = self._repo.buscar_piquete(origem)
            if any(p_origem.animais[c] < q for c, q in quantidades.items()):
                raise ValueError("Quantidade insuficiente na origem.")
            for c, q in quantidades.items():
                p_origem.animais[c] -= q
        if tipo in ("adicionar", "mover"):
            p_destino = self._repo.buscar_piquete(destino)
            for c, q in quantidades.items():
                p_destino.animais[c] += q

    # ---- IMonitoramento ----
    def atualizar_ndvi(self, piquete_id: int, hoje: date) -> LeituraNDVI | None:
        piquete = self._repo.buscar_piquete(piquete_id)
        try:
            leitura = self._satelite.obter_ndvi(piquete.poligono, hoje)
        except LookupError:
            print(f"    {piquete.nome}: satelite sem imagem para o periodo.")
            return self._repo.ultima_leitura(piquete_id)
        if leitura.nuvem > self.NUVEM_MAXIMA:
            anterior = self._repo.ultima_leitura(piquete_id)
            quando = anterior.data.strftime("%d/%m") if anterior else "nenhuma"
            print(f"    [R6] {piquete.nome}: imagem com {leitura.nuvem:.0%} de nuvem descartada; "
                  f"vale a ultima leitura limpa ({quando}).")
            return anterior
        self._repo.salvar_leitura(piquete_id, leitura)
        return leitura

    def leitura_valida(self, piquete_id: int, hoje: date) -> LeituraNDVI | None:
        leitura = self._repo.ultima_leitura(piquete_id)
        if leitura is None or (hoje - leitura.data).days > self.VALIDADE_DIAS:
            return None
        return leitura


# ---------------- CORE ----------------

class AgenteDeManejo:
    """EAP 1.1 - Agente inteligente: analisa o piquete e recomenda o manejo.

    A decisao (acao) e de uma regra deterministica; o Gemini so escreve o texto.
    O validador barra o texto que contradiz a regra (risco R3)."""
    CAMADA, EAP, GANTT = "core", "1.1", (6, 7)
    FORNECE, REQUER = ("IRecomendacao",), ("ICadastro", "IMonitoramento", "IClima", "ILLM", "IRepositorio")

    # Faixas de exemplo, a validar com a bibliografia (criterio de qualidade 1.1.3)
    FAIXAS_NDVI = ((0.30, "degradada"), (0.50, "baixa"), (0.70, "boa"), (1.01, "otima"))

    def __init__(self, cadastro: ICadastro, monitoramento: IMonitoramento, clima: IClima,
                 llm: ILLM, repo: IRepositorio) -> None:
        self._cadastro, self._monit, self._clima = cadastro, monitoramento, clima
        self._llm, self._repo = llm, repo

    def classificar(self, ndvi: float) -> str:
        return next(nome for limite, nome in self.FAIXAS_NDVI if ndvi < limite)

    def decidir(self, piquete: Piquete, leitura: LeituraNDVI | None) -> str:
        if leitura is None:
            return "SEM_DADOS"
        faixa = self.classificar(leitura.ndvi)
        ocupado = piquete.lotacao > 0
        if ocupado:
            return "RETIRAR" if faixa in ("degradada", "baixa") else "MANTER"
        return "PODE_RECEBER" if faixa in ("boa", "otima") else "DESCANSAR"

    def recomendar(self, piquete_id: int, hoje: date) -> Recomendacao:
        piquete = self._cadastro.buscar(piquete_id)
        leitura = self._monit.leitura_valida(piquete_id, hoje)
        acao = self.decidir(piquete, leitura)
        if acao == "SEM_DADOS":
            rec = Recomendacao(piquete_id, acao, "Sem leitura NDVI valida nos ultimos 7 dias.", "regra", hoje)
            self._repo.salvar_recomendacao(rec)
            return rec

        clima = self._clima.previsao(piquete.centroide)
        lotacao_ha = piquete.lotacao / (piquete.area_m2 / 10_000)
        prompt = (f"Piquete {piquete.nome}. NDVI {leitura.ndvi:.2f} ({self.classificar(leitura.ndvi)}), "
                  f"lotacao {lotacao_ha:.1f} cab/ha, chuva prevista em 7 dias {clima.chuva_7d_mm:.0f} mm. "
                  f"A acao decidida e {acao}. Explique ao pecuarista em uma frase.")
        texto_padrao = f"{acao}: NDVI {leitura.ndvi:.2f}, {lotacao_ha:.1f} cab/ha, chuva 7d {clima.chuva_7d_mm:.0f} mm."
        try:
            texto = self._llm.gerar_texto(prompt)
            origem = "gemini"
            if not texto.upper().startswith(acao):  # validador do risco R3
                print(f"    [R3] {piquete.nome}: IA respondeu '{texto.split('.')[0]}', "
                      f"mas a regra decidiu {acao}. Texto da IA descartado.")
                texto, origem = texto_padrao, "regra"
        except CotaEsgotada:
            print(f"    [R7] {piquete.nome}: cota esgotada, usando o texto padrao.")
            texto, origem = texto_padrao, "regra"
        rec = Recomendacao(piquete_id, acao, texto, origem, hoje)
        self._repo.salvar_recomendacao(rec)
        return rec


# ---------------- GENERIC ----------------

class Autenticacao:
    """EAP 4.2 - Autenticacao de usuario."""
    CAMADA, EAP, GANTT = "generic", "4.2", (3,)
    FORNECE, REQUER = ("IAutenticacao",), ("IRepositorio",)
    VALIDADE = timedelta(hours=8)

    def __init__(self, repo: IRepositorio) -> None:
        self._repo = repo
        self._sessoes: dict[str, tuple[str, datetime]] = {}

    @staticmethod
    def _hash(senha: str, sal: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, 100_000)

    def registrar(self, email: str, senha: str) -> None:
        sal = secrets.token_bytes(16)
        self._repo.salvar_usuario(email, {"sal": sal, "hash": self._hash(senha, sal)})

    def login(self, email: str, senha: str) -> str:
        usuario = self._repo.buscar_usuario(email)
        if usuario is None or not secrets.compare_digest(usuario["hash"], self._hash(senha, usuario["sal"])):
            raise AcessoNegado("E-mail ou senha incorretos.")
        token = secrets.token_urlsafe(24)
        self._sessoes[token] = (email, datetime.now() + self.VALIDADE)
        return token

    def validar(self, token: str) -> str:
        sessao = self._sessoes.get(token)
        if sessao is None or sessao[1] < datetime.now():
            raise AcessoNegado("401: token ausente ou expirado.")
        return sessao[0]


class HistoricoDashboard:
    """EAP 4.1 - Historico e dashboard."""
    CAMADA, EAP, GANTT = "generic", "4.1", (8,)
    FORNECE, REQUER = ("IDashboard",), ("ICadastro", "IRepositorio")

    def __init__(self, cadastro: ICadastro, repo: IRepositorio) -> None:
        self._cadastro, self._repo = cadastro, repo

    def consultar(self) -> list[dict]:
        linhas = []
        for p in self._cadastro.listar():
            leitura = self._repo.ultima_leitura(p.id)
            historico = self._repo.historico(p.id)
            ultima = historico[-1] if historico else None
            linhas.append({
                "piquete": p.nome,
                "lotacao": p.lotacao,
                "animais": dict(p.animais),
                "ndvi": f"{leitura.ndvi:.2f} em {leitura.data:%d/%m}" if leitura else "sem leitura",
                "recomendacao": f"{ultima.texto} [{ultima.origem}]" if ultima else "-",
            })
        return linhas


# ---------------- APLICACOES (pontos de entrada) ----------------

class AplicacaoWeb:
    """Tela do pecuarista (EAP 4.3 Configuracao de UI). Roda no navegador; toda chamada leva o token."""
    CAMADA, EAP, GANTT = "aplicacao", "4.3", (3, 8)
    FORNECE, REQUER = (), ("IAutenticacao", "ICadastro", "IOcupacao", "IDashboard")

    def __init__(self, auth: IAutenticacao, cadastro: ICadastro, ocupacao: IOcupacao, dashboard: IDashboard) -> None:
        self._auth, self._cadastro, self._ocupacao, self._dashboard = auth, cadastro, ocupacao, dashboard

    def cadastrar_piquete(self, token: str, nome: str, poligono: list, area_m2: float) -> int:
        self._auth.validar(token)
        return self._cadastro.cadastrar_piquete(nome, poligono, area_m2)

    def movimentar(self, token: str, tipo: str, origem: int | None, destino: int | None, qtd: dict) -> None:
        self._auth.validar(token)
        self._ocupacao.movimentar(tipo, origem, destino, qtd)

    def dashboard(self, token: str) -> list[dict]:
        self._auth.validar(token)
        return self._dashboard.consultar()


class AgendadorDaRotina:
    """Rotina agendada a cada X dias (cron): atualiza o NDVI e gera as recomendacoes."""
    CAMADA, EAP, GANTT = "aplicacao", "2.1", (4, 9)
    FORNECE, REQUER = (), ("ICadastro", "IMonitoramento", "IRecomendacao")

    def __init__(self, cadastro: ICadastro, monitoramento: IMonitoramento, agente: IRecomendacao) -> None:
        self._cadastro, self._monit, self._agente = cadastro, monitoramento, agente

    def executar(self, hoje: date) -> list[Recomendacao]:
        recomendacoes = []
        for p in self._cadastro.listar():
            self._monit.atualizar_ndvi(p.id, hoje)
            recomendacoes.append(self._agente.recomendar(p.id, hoje))
        return recomendacoes


# ======================================================================
# PARTE 4 - MONTAGEM (os conectores do DC)
# ======================================================================

COMPONENTES = (RepositorioPostgres, AdaptadorSentinel, AdaptadorOpenMeteo, AdaptadorGemini,
               Cadastros, Monitoramento, AgenteDeManejo, Autenticacao, HistoricoDashboard,
               AplicacaoWeb, AgendadorDaRotina)


def conferir_componentes() -> None:
    """Toda interface requerida precisa ser fornecida por algum componente."""
    fornecidas = {i: c.__name__ for c in COMPONENTES for i in c.FORNECE}
    for c in COMPONENTES:
        faltando = [i for i in c.REQUER if i not in fornecidas]
        if faltando:
            raise RuntimeError(f"{c.__name__} requer {faltando}, que ninguem fornece.")


@dataclass
class Sistema:
    auth: Autenticacao
    web: AplicacaoWeb
    rotina: AgendadorDaRotina
    cota: ControleDeCota


def montar_sistema(satelite: ISatelite, cota_gemini: int) -> Sistema:
    conferir_componentes()
    repo = RepositorioPostgres()
    cota = ControleDeCota(cota_gemini)
    clima, llm = AdaptadorOpenMeteo(), AdaptadorGemini(cota)
    cadastros = Cadastros(repo)
    monit = Monitoramento(satelite, repo)
    agente = AgenteDeManejo(cadastros, monit, clima, llm, repo)
    auth = Autenticacao(repo)
    dashboard = HistoricoDashboard(cadastros, repo)
    web = AplicacaoWeb(auth, cadastros, monit, dashboard)
    rotina = AgendadorDaRotina(cadastros, monit, agente)
    return Sistema(auth, web, rotina, cota)


# ======================================================================
# PARTE 5 - IMPLANTACAO (o DI em codigo)
# ======================================================================

@dataclass(frozen=True)
class Artefato:
    nome: str
    manifesta: tuple[type, ...] = ()


@dataclass(frozen=True)
class No:
    nome: str
    estereotipo: str
    ambiente: str
    artefatos: tuple[Artefato, ...] = ()


WEB = Artefato("maneja-web (HTML/JS)", (AplicacaoWeb,))

NOS = (
    No("Computador do Pecuarista", "device", "Navegador web", (WEB,)),
    No("Celular / Tablet no campo", "device", "Navegador movel", (WEB,)),
    No("Servidor de Aplicacao", "Render Web Service", "Python 3.12 + Uvicorn", (
        Artefato("maneja-api", (Autenticacao, Cadastros, Monitoramento, AgenteDeManejo,
                                HistoricoDashboard, RepositorioPostgres, AdaptadorSentinel,
                                AdaptadorOpenMeteo, AdaptadorGemini)),
        Artefato("maneja-web (arquivos estaticos)"),
    )),
    No("Servidor de Rotina", "Render Cron Job", "Python 3.12", (Artefato("rotina_ndvi.py", (AgendadorDaRotina,)),)),
    No("Servidor de Banco", "Render PostgreSQL", "PostgreSQL 16", (Artefato("maneja_db (schema.sql)"),)),
    No("Google Earth Engine", "servico externo", "Sentinel-2"),
    No("Open-Meteo", "servico externo", "API REST"),
    No("Google Gemini API", "servico externo", "API REST"),
)

CONEXOES = (
    ("Computador do Pecuarista", "Servidor de Aplicacao", "HTTPS - REST/JSON + token"),
    ("Celular / Tablet no campo", "Servidor de Aplicacao", "HTTPS - REST/JSON + token"),
    ("Servidor de Rotina", "Servidor de Aplicacao", "HTTPS - POST /rotinas/ndvi"),
    ("Servidor de Aplicacao", "Servidor de Banco", "TCP 5432 - SQL com TLS"),
    ("Servidor de Aplicacao", "Google Earth Engine", "HTTPS"),
    ("Servidor de Aplicacao", "Open-Meteo", "HTTPS"),
    ("Servidor de Aplicacao", "Google Gemini API", "HTTPS"),
)


def conferir_implantacao() -> None:
    """O DI precisa bater com o DC:
    1. todo componente esta em algum artefato implantado;
    2. se um componente requer uma interface fornecida em OUTRO no, existe conexao entre os nos;
    3. todo adaptador tem conexao com o servico externo que ele usa."""
    onde: dict[type, set[str]] = {}
    for no in NOS:
        for art in no.artefatos:
            for comp in art.manifesta:
                onde.setdefault(comp, set()).add(no.nome)
    ligados = {frozenset((a, b)) for a, b, _ in CONEXOES}

    for comp in COMPONENTES:
        if comp not in onde:
            raise RuntimeError(f"{comp.__name__} nao esta implantado em nenhum no.")

    for comp in COMPONENTES:
        for interface in comp.REQUER:
            fornecedor = next(c for c in COMPONENTES if interface in c.FORNECE)
            for no_a in onde[comp]:
                for no_b in onde[fornecedor]:
                    if no_a != no_b and frozenset((no_a, no_b)) not in ligados:
                        raise RuntimeError(f"Falta conexao {no_a} -> {no_b} ({comp.__name__} requer {interface}).")

    for comp in COMPONENTES:
        externo = getattr(comp, "NO_EXTERNO", None)
        if externo and not any(frozenset((n, externo)) in ligados for n in onde[comp]):
            raise RuntimeError(f"{comp.__name__} precisa de conexao com {externo}.")


# ======================================================================
# PARTE 6 - SIMULACAO
# ======================================================================

def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")


if __name__ == "__main__":
    hoje = date(2026, 11, 19)

    titulo("1. Conferencia do DC e do DI")
    conferir_componentes()
    conferir_implantacao()
    print("Todas as interfaces requeridas tem fornecedor e todos os nos que conversam estao conectados.")
    for camada in ("aplicacao", "core", "support", "generic", "infra"):
        nomes = [f"{c.__name__} (EAP {c.EAP}, Gantt {', '.join(map(str, c.GANTT))})"
                 for c in COMPONENTES if c.CAMADA == camada]
        print(f"  {camada:<9} {'; '.join(nomes)}")

    titulo("2. Onde cada componente roda (DI)")
    for no in NOS:
        print(f"  <<{no.estereotipo}>> {no.nome} [{no.ambiente}]")
        for art in no.artefatos:
            comps = ", ".join(c.__name__ for c in art.manifesta) or "-"
            print(f"      <<artifact>> {art.nome}: {comps}")

    titulo("3. Aquisicoes por tras dos adaptadores")
    for comp in COMPONENTES:
        if hasattr(comp, "AQUISICAO"):
            aq, fornecedor, plano = comp.AQUISICAO
            print(f"  {aq} {comp.__name__:<20} fornecedor: {fornecedor} ({plano})")

    # Simulacao do satelite: o Piquete Norte tem imagem limpa; o Piquete Sul so tem
    # imagem encoberta hoje (risco R6), entao vale a leitura limpa de 4 dias atras.
    norte = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    sul = [(200.0, 0.0), (300.0, 0.0), (300.0, 120.0), (200.0, 120.0)]
    cenas = {
        (50.0, 50.0): [LeituraNDVI(0.42, 0.05, hoje)],
        (250.0, 60.0): [LeituraNDVI(0.74, 0.10, hoje - timedelta(days=4)),
                        LeituraNDVI(0.20, 0.85, hoje)],
    }
    sistema = montar_sistema(AdaptadorSentinel(cenas), cota_gemini=3)

    titulo("4. Login e cadastro (Aplicacao Web -> Servidor de Aplicacao)")
    try:
        sistema.web.dashboard("token-falso")
    except AcessoNegado as erro:
        print(f"  Sem login: {erro}")
    sistema.auth.registrar("pecuarista@fazenda.com", "capim123")
    token = sistema.auth.login("pecuarista@fazenda.com", "capim123")
    p_norte = sistema.web.cadastrar_piquete(token, "Piquete Norte", norte, 10_000)
    p_sul = sistema.web.cadastrar_piquete(token, "Piquete Sul", sul, 12_000)
    sistema.web.cadastrar_piquete(token, "Piquete Leste", [(400, 0), (450, 0), (450, 50)], 1_250)
    print("  3 piquetes cadastrados (o Leste ainda nao tem imagem de satelite).")

    titulo("5. Rotina agendada de 4 dias atras (piquetes ainda vazios)")
    for rec in sistema.rotina.executar(hoje - timedelta(days=4)):
        print(f"  Piquete {rec.piquete_id}: {rec.acao:<12} via {rec.origem}")

    titulo("6. Movimentacao de animais")
    sistema.web.movimentar(token, "adicionar", None, p_norte, {"bois": 10, "vacas": 5, "bezerros": 2})
    sistema.web.movimentar(token, "mover", p_norte, p_sul, {"bois": 3})
    print("  Norte recebeu 17 animais; 3 bois foram para o Sul.")
    try:
        sistema.web.movimentar(token, "adicionar", None, p_norte, {"bois": -5})
    except ValueError as erro:
        print(f"  Barrado (criterio 2.2.1, lotacao nunca negativa): {erro}")

    titulo("7. Rotina agendada de hoje (Servidor de Rotina -> Servidor de Aplicacao)")
    for rec in sistema.rotina.executar(hoje):
        print(f"  Piquete {rec.piquete_id}: {rec.acao:<12} via {rec.origem}")

    titulo("8. Dashboard")
    for linha in sistema.web.dashboard(token):
        print(f"  {linha['piquete']}: lotacao {linha['lotacao']} {linha['animais']}")
        print(f"      NDVI {linha['ndvi']} | {linha['recomendacao']}")
