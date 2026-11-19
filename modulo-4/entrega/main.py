"""
Manejo Inteligente de Bois - Modulo 4
Snippet que implementa o Diagrama de Sequencia (DS) e o Diagrama de Estados (DE).

Cada metodo traz o nome da mensagem do DS que ele implementa.
O DE vira duas enumeracoes e uma tabela de transicoes permitidas.
Satelite e Gemini sao simulados: roda sem internet e sem chave.

Ementa do modulo 4 no codigo:
  - Gestao de qualidade: os criterios de aceitacao 2.2.1, 3.1 e 3.2 viram verificacoes
    automaticas (verificar_criterios_de_qualidade).
  - Gestao de RH: cada parte traz o papel responsavel e o verificador, como na Matriz RACI
    de qualidade (GER, FRN, BCK, MID).
"""

from dataclasses import dataclass, field
from enum import Enum

CATEGORIAS = ("bois", "vacas", "bezerros")


# ======================================================================
# DIAGRAMA DE ESTADOS
# Estado composto "Piquete ativo" com duas regioes concorrentes:
# a ocupacao (muda pelas movimentacoes) e o monitoramento NDVI (muda pela rotina).
# ======================================================================

class EstadoOcupacao(Enum):
    VAZIO = "Vazio"
    OCUPADO = "Ocupado"


class EstadoNDVI(Enum):
    SEM_LEITURA = "Sem leitura NDVI"
    COLETANDO = "Coletando imagem"
    GERANDO = "Gerando recomendacao"
    COM_RECOMENDACAO = "Com recomendacao"


# Transicoes da regiao NDVI, uma por seta do DE
TRANSICOES_NDVI = {
    (EstadoNDVI.SEM_LEITURA, EstadoNDVI.COLETANDO): "dispararAtualizacaoNDVI() / solicitarImagem()",
    (EstadoNDVI.COLETANDO, EstadoNDVI.GERANDO): "imagem e NDVI recebidos / salvarLeituraNDVI()",
    (EstadoNDVI.GERANDO, EstadoNDVI.COM_RECOMENDACAO): "recomendacao recebida / salvarRecomendacao()",
    (EstadoNDVI.COM_RECOMENDACAO, EstadoNDVI.COLETANDO): "dispararAtualizacaoNDVI() [a cada X dias]",
}


# ======================================================================
# MODELO DE DADOS DO PIQUETE
# ======================================================================

@dataclass
class Piquete:
    id: int
    poligono: list
    area_m2: float
    animais: dict = field(default_factory=lambda: dict.fromkeys(CATEGORIAS, 0))

    estado_ndvi: EstadoNDVI = EstadoNDVI.SEM_LEITURA
    ndvi: float = None
    recomendacao: str = None

    @property
    def lotacao(self):
        return sum(self.animais.values())

    @property
    def estado_ocupacao(self):
        # Regiao de ocupacao do DE: Vazio [lotacao = 0] / Ocupado [lotacao > 0]
        if self.lotacao == 0:
            return EstadoOcupacao.VAZIO
        return EstadoOcupacao.OCUPADO

    def mudar_estado_ndvi(self, novo):
        # So aceita as setas que existem no DE
        if (self.estado_ndvi, novo) not in TRANSICOES_NDVI:
            raise RuntimeError(
                f"Transicao invalida no DE: {self.estado_ndvi.value} -> {novo.value}"
            )
        self.estado_ndvi = novo


# ======================================================================
# SERVICOS EXTERNOS SIMULADOS (participantes da direita do DS)
# Responsavel: MID (Maria Antonia) · verificador: BCK
# ======================================================================

class ServicoSatelite:

    def solicitar_imagem(self, poligono, data="hoje"):
        # DS 21-22: solicitarImagem(poligono, data) -> imagemSatelite, ndvi
        print("Solicitando imagem ao satelite...")
        return "imagem_satelite", 0.72


class ServicoGemini:

    def generate_content(self, prompt):
        # DS 27-28: generateContent(prompt) -> recomendacaoManejo
        print("Enviando dados ao Gemini...")
        return "Pastagem em boas condicoes. Monitorar lotacao."


# ======================================================================
# BANCO DE DADOS (participante do DS) · Responsavel: BCK (Kaue)
# ======================================================================

class BancoDeDados:

    def __init__(self):
        self.piquetes = {}
        self.leituras = []

    def salvar_piquete(self, piquete):        # DS 4-5
        self.piquetes[piquete.id] = piquete
        return piquete.id

    def listar_piquetes(self):                # DS 19-20
        return list(self.piquetes.values())

    def salvar_leitura_ndvi(self, piquete_id, ndvi, data):  # DS 23
        self.leituras.append((piquete_id, ndvi, data))

    def buscar_lotacao(self, piquete_id):     # DS 24-25
        return dict(self.piquetes[piquete_id].animais)

    def salvar_recomendacao(self, piquete_id, recomendacao):  # DS 29
        self.piquetes[piquete_id].recomendacao = recomendacao

    def buscar_ndvi_e_recomendacoes(self):    # DS 33-34
        return self.listar_piquetes()


# ======================================================================
# API / LOGICA DO SISTEMA · Responsavel: BCK (Kaue) · verificador: FRN
# ======================================================================

class SistemaPiquetes:

    def __init__(self):
        self.banco = BancoDeDados()
        self.proximo_id = 1
        self.satelite = ServicoSatelite()
        self.gemini = ServicoGemini()

    @property
    def piquetes(self):
        return self.banco.piquetes

    # 1. CADASTRO DE PIQUETE (DS 1-7; DE: Em cadastro -> Piquete ativo)

    def validar_poligono_e_area(self, poligono, area_m2):
        # DS 2: validarPoligonoEArea(). Criterio de qualidade 3.1
        return (
            isinstance(poligono, list)
            and len(set(poligono)) >= 3
            and area_m2 > 0
        )

    def cadastrar_piquete(self, poligono, area_m2):
        # DS 3: POST /piquetes. DE: [invalido] / exibe erro  |  [valido] / salvarPiquete()
        if not self.validar_poligono_e_area(poligono, area_m2):
            raise ValueError("Poligono ou area invalida.")

        piquete = Piquete(id=self.proximo_id, poligono=poligono, area_m2=area_m2)
        self.banco.salvar_piquete(piquete)
        self.proximo_id += 1

        print(f"Piquete {piquete.id} cadastrado.")
        return piquete.id

    # 2. MOVIMENTACAO DE ANIMAIS (DS 8-17)

    def validar_quantidades(self, quantidades):
        # DS 9: validarQuantidades(). Criterio de qualidade 3.2:
        # quantidade inteira e nao negativa, so das categorias cadastradas
        for tipo, quantidade in quantidades.items():
            if tipo not in CATEGORIAS:
                raise ValueError(f"Categoria desconhecida: {tipo}.")
            if not isinstance(quantidade, int) or quantidade < 0:
                raise ValueError(f"Quantidade invalida: {tipo}={quantidade}.")

    def incrementar_animais(self, piquete_id, quantidades):
        # DS 11 e 14. DE: Vazio -> Ocupado
        self.validar_quantidades(quantidades)
        piquete = self.piquetes[piquete_id]
        for tipo, quantidade in quantidades.items():
            piquete.animais[tipo] += quantidade
        print("Animais adicionados ao piquete.")

    def decrementar_animais(self, piquete_id, quantidades):
        # DS 12 e 13. DE: Ocupado -> Vazio [lotacao = 0]
        self.validar_quantidades(quantidades)
        piquete = self.piquetes[piquete_id]
        for tipo, quantidade in quantidades.items():
            if piquete.animais[tipo] < quantidade:
                raise ValueError("Quantidade insuficiente no piquete.")
        for tipo, quantidade in quantidades.items():
            piquete.animais[tipo] -= quantidade
        print("Animais removidos do piquete.")

    def movimentar_animais(self, tipo, origem, destino, quantidades):
        # DS 10: POST /movimentacoes, com o bloco alt do DS
        if tipo == "adicionar":
            self.incrementar_animais(destino, quantidades)
        elif tipo == "remover":
            self.decrementar_animais(origem, quantidades)
        elif tipo == "mover":
            self.decrementar_animais(origem, quantidades)  # valida a origem antes
            self.incrementar_animais(destino, quantidades)
        else:
            raise ValueError("Tipo de movimentacao invalido.")

    # 3. ATUALIZACAO AUTOMATICA DO NDVI (DS 18-30, rotina agendada)

    def montar_prompt(self, ndvi, area_m2, animais):
        # DS 26: montarPrompt(ndvi, areaM2, lotacao)
        return (f"NDVI: {ndvi}, Area: {area_m2}, "
                f"Lotacao: {sum(animais.values())}, Animais: {animais}")

    def disparar_atualizacao_ndvi(self, data="hoje"):
        # DS 18: dispararAtualizacaoNDVI(), chamado pelo Agendador (Cron)
        for piquete in self.banco.listar_piquetes():          # loop [para cada piquete]
            piquete.mudar_estado_ndvi(EstadoNDVI.COLETANDO)
            imagem, ndvi = self.satelite.solicitar_imagem(piquete.poligono, data)

            piquete.ndvi = ndvi
            self.banco.salvar_leitura_ndvi(piquete.id, ndvi, data)
            piquete.mudar_estado_ndvi(EstadoNDVI.GERANDO)

            animais = self.banco.buscar_lotacao(piquete.id)
            prompt = self.montar_prompt(ndvi, piquete.area_m2, animais)
            recomendacao = self.gemini.generate_content(prompt)

            self.banco.salvar_recomendacao(piquete.id, recomendacao)
            piquete.mudar_estado_ndvi(EstadoNDVI.COM_RECOMENDACAO)
            print(f"Piquete {piquete.id}: recomendacao salva.")

    # 4. CONSULTA DO DASHBOARD (DS 31-37) · Responsavel: FRN (Joao Pedro) · verificador: GER

    def consultar_dashboard(self):
        # DS 32: GET /dashboard  ->  DS 36: renderizarMapaNDVI()
        for piquete in self.banco.buscar_ndvi_e_recomendacoes():
            print(f"\nPiquete {piquete.id}")
            print(f"Area: {piquete.area_m2} m2")
            print(f"Lotacao: {piquete.lotacao}")
            print(f"Animais: {piquete.animais}")
            print(f"Ocupacao: {piquete.estado_ocupacao.value}")
            print(f"NDVI: {piquete.ndvi}")
            print(f"Estado NDVI: {piquete.estado_ndvi.value}")
            print(f"Recomendacao: {piquete.recomendacao}")


# ======================================================================
# GESTAO DE QUALIDADE: criterios de aceitacao como verificacoes automaticas
# ======================================================================

def deve_falhar(funcao, *args):
    try:
        funcao(*args)
    except (ValueError, RuntimeError):
        return True
    return False


def verificar_criterios_de_qualidade():
    s = SistemaPiquetes()
    p1 = s.cadastrar_piquete([(0, 0), (10, 0), (10, 10)], 10000)
    p2 = s.cadastrar_piquete([(20, 20), (30, 20), (30, 30)], 12000)
    s.movimentar_animais("adicionar", None, p1, {"bois": 10, "vacas": 5, "bezerros": 2})
    rebanho = 17

    resultados = {
        # 3.1 Cadastro de Piquete: poligono invalido rejeitado
        "3.1 poligono com 2 pontos rejeitado": deve_falhar(s.cadastrar_piquete, [(0, 0), (1, 1)], 100),
        "3.1 area zero rejeitada": deve_falhar(s.cadastrar_piquete, [(0, 0), (1, 0), (1, 1)], 0),
        # 3.2 Cadastro de Bois: quantidade inteira e nao negativa
        "3.2 quantidade negativa rejeitada": deve_falhar(s.movimentar_animais, "adicionar", None, p1, {"bois": -5}),
        "3.2 quantidade fracionada rejeitada": deve_falhar(s.movimentar_animais, "adicionar", None, p1, {"vacas": 1.5}),
        "3.2 categoria desconhecida rejeitada": deve_falhar(s.movimentar_animais, "adicionar", None, p1, {"cavalos": 1}),
        # 2.2.1 Estimativa de Ocupacao: rebanho se conserva e lotacao nunca fica negativa
        "2.2.1 mover mais do que existe rejeitado": deve_falhar(s.movimentar_animais, "mover", p1, p2, {"bois": 99}),
    }
    s.movimentar_animais("mover", p1, p2, {"bois": 3})
    total = sum(p.lotacao for p in s.piquetes.values())
    resultados["2.2.1 soma das lotacoes = rebanho"] = total == rebanho
    resultados["2.2.1 nenhuma lotacao negativa"] = all(
        q >= 0 for p in s.piquetes.values() for q in p.animais.values()
    )
    # DE: so as setas do diagrama sao aceitas
    resultados["DE transicao fora do diagrama rejeitada"] = deve_falhar(
        s.piquetes[p1].mudar_estado_ndvi, EstadoNDVI.COM_RECOMENDACAO
    )
    return resultados


# ======================================================================
# SIMULACAO DO FUNCIONAMENTO DO SISTEMA
# ======================================================================

if __name__ == "__main__":

    sistema = SistemaPiquetes()

    p1 = sistema.cadastrar_piquete([(0, 0), (10, 0), (10, 10)], 10000)
    p2 = sistema.cadastrar_piquete([(20, 20), (30, 20), (30, 30)], 12000)

    sistema.movimentar_animais("adicionar", None, p1, {"bois": 10, "vacas": 5, "bezerros": 2})
    sistema.movimentar_animais("mover", p1, p2, {"bois": 3, "vacas": 0, "bezerros": 0})

    sistema.disparar_atualizacao_ndvi()
    sistema.consultar_dashboard()

    print("\n=== Criterios de qualidade ===")
    resultados = verificar_criterios_de_qualidade()
    for criterio, ok in resultados.items():
        print(f"[{'OK' if ok else 'FALHOU'}] {criterio}")
    print(f"{sum(resultados.values())}/{len(resultados)} verificacoes aprovadas")
