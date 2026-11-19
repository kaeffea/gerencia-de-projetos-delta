
from dataclasses import dataclass, field
from enum import Enum

# DIAGRAMA DE ESTADOS

class EstadoOcupacao(Enum):
    VAZIO = "Vazio"
    OCUPADO = "Ocupado"


class EstadoNDVI(Enum):
    SEM_LEITURA = "Sem leitura NDVI"
    COLETANDO = "Coletando imagem"
    GERANDO = "Gerando recomendacao"
    COM_RECOMENDACAO = "Com recomendacao"


# MODELO DE DADOS DO PIQUETE

@dataclass
class Piquete:
    id: int
    poligono: list
    area_m2: float
    animais: dict = field(default_factory=lambda: {
        "bois": 0,
        "vacas": 0,
        "bezerros": 0
    })

    estado_ndvi: EstadoNDVI = EstadoNDVI.SEM_LEITURA
    ndvi: float = None
    recomendacao: str = None

    @property
    def lotacao(self):
        return sum(self.animais.values())

    @property
    def estado_ocupacao(self):
        if self.lotacao == 0:
            return EstadoOcupacao.VAZIO
        return EstadoOcupacao.OCUPADO


# SERVIÇOS EXTERNOS SIMULADOS

class ServicoSatelite:

    def solicitar_imagem(self, poligono):
        print("Solicitando imagem ao satelite...")

        # Simulacao do recebimento da imagem e do NDVI
        imagem = "imagem_satelite"
        ndvi = 0.72

        return imagem, ndvi


class ServicoGemini:

    def gerar_recomendacao(self, prompt):
        print("Enviando dados ao Gemini...")

        # Simulacao da resposta da IA
        return "Pastagem em boas condicoes. Monitorar lotacao."


# API / LOGICA DO SISTEMA

class SistemaPiquetes:

    def __init__(self):
        self.piquetes = {}
        self.proximo_id = 1

        self.satelite = ServicoSatelite()
        self.gemini = ServicoGemini()

    # 1. CADASTRO DE PIQUETE

    def validar_poligono_e_area(self, poligono, area_m2):
        return (
            isinstance(poligono, list)
            and len(poligono) >= 3
            and area_m2 > 0
        )

    def cadastrar_piquete(self, poligono, area_m2):

        if not self.validar_poligono_e_area(poligono, area_m2):
            raise ValueError("Poligono ou area invalida.")

        piquete = Piquete(
            id=self.proximo_id,
            poligono=poligono,
            area_m2=area_m2
        )

        self.piquetes[piquete.id] = piquete
        self.proximo_id += 1

        print(f"Piquete {piquete.id} cadastrado.")
        return piquete.id

    # 2. MOVIMENTACAO DE ANIMAIS

    def incrementar_animais(self, piquete_id, quantidades):

        piquete = self.piquetes[piquete_id]

        for tipo, quantidade in quantidades.items():
            piquete.animais[tipo] += quantidade

        print("Animais adicionados ao piquete.")

    def decrementar_animais(self, piquete_id, quantidades):

        piquete = self.piquetes[piquete_id]

        for tipo, quantidade in quantidades.items():
            if quantidade < 0 or piquete.animais[tipo] < quantidade:
                raise ValueError("Quantidade de animais invalida.")

        for tipo, quantidade in quantidades.items():
            piquete.animais[tipo] -= quantidade

        print("Animais removidos do piquete.")

    def movimentar_animais(
        self, tipo, origem, destino, quantidades
    ):

        if tipo == "adicionar":
            self.incrementar_animais(destino, quantidades)

        elif tipo == "remover":
            self.decrementar_animais(origem, quantidades)

        elif tipo == "mover":
            # Valida a origem antes de alterar os dois piquetes
            piquete_origem = self.piquetes[origem]

            for especie, quantidade in quantidades.items():
                if quantidade < 0 or piquete_origem.animais[especie] < quantidade:
                    raise ValueError("Quantidade insuficiente na origem.")

            self.decrementar_animais(origem, quantidades)
            self.incrementar_animais(destino, quantidades)

        else:
            raise ValueError("Tipo de movimentacao invalido.")

    # 3. ATUALIZACAO AUTOMATICA DO NDVI

    def disparar_atualizacao_ndvi(self):

        for piquete in self.piquetes.values():

            piquete.estado_ndvi = EstadoNDVI.COLETANDO

            imagem, ndvi = self.satelite.solicitar_imagem(
                piquete.poligono
            )

            piquete.ndvi = ndvi

            # Recebimento da imagem e do NDVI
            piquete.estado_ndvi = EstadoNDVI.GERANDO

            prompt = (
                f"NDVI: {ndvi}, "
                f"Area: {piquete.area_m2}, "
                f"Lotacao: {piquete.lotacao}, "
                f"Animais: {piquete.animais}"
            )

            recomendacao = self.gemini.gerar_recomendacao(prompt)

            piquete.recomendacao = recomendacao
            piquete.estado_ndvi = EstadoNDVI.COM_RECOMENDACAO

            print(f"Piquete {piquete.id}: recomendacao salva.")

    # 4. CONSULTA DO DASHBOARD

    def consultar_dashboard(self):

        for piquete in self.piquetes.values():

            print(f"\nPiquete {piquete.id}")
            print(f"Area: {piquete.area_m2} m2")
            print(f"Lotacao: {piquete.lotacao}")
            print(f"Animais: {piquete.animais}")
            print(f"Ocupacao: {piquete.estado_ocupacao.value}")
            print(f"NDVI: {piquete.ndvi}")
            print(f"Estado NDVI: {piquete.estado_ndvi.value}")
            print(f"Recomendacao: {piquete.recomendacao}")

# SIMULACAO DO FUNCIONAMENTO DO SISTEMA

if __name__ == "__main__":

    sistema = SistemaPiquetes()

    # Cadastro de dois piquetes
    p1 = sistema.cadastrar_piquete(
        [(0, 0), (10, 0), (10, 10)],
        10000
    )

    p2 = sistema.cadastrar_piquete(
        [(20, 20), (30, 20), (30, 30)],
        12000
    )

    # Adicionar animais ao primeiro piquete
    sistema.movimentar_animais(
        "adicionar",
        None,
        p1,
        {"bois": 10, "vacas": 5, "bezerros": 2}
    )

    # Mover animais do primeiro para o segundo
    sistema.movimentar_animais(
        "mover",
        p1,
        p2,
        {"bois": 3, "vacas": 0, "bezerros": 0}
    )

    # Executar rotina de monitoramento
    sistema.disparar_atualizacao_ndvi()

    # Consultar dashboard
    sistema.consultar_dashboard()
