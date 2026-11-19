# Módulo 5 · o que entregar e como apresentar

## Anexar no Classroom

- `Módulo5.pdf`: o pitch (13 slides)
- `main.py`: o snippet (roda com `python main.py`, sem instalar nada)
- `render.yaml`: o Diagrama de Implantação como código
- `diagramas/`: os dois diagramas em PNG (e SVG, se precisarem editar)
- `saida-do-teste.txt`: a saída do `main.py`

Para editar os slides, mexa em `slides/slides.html` e gere o PDF de novo pelo Chrome (Imprimir > Salvar como PDF, sem margens).

## Roteiro do pitch (cerca de 1 minuto por slide)

1. **Capa.**
2. **Diagrama de Componentes.** 11 componentes em 4 camadas. A bolinha é o que o componente oferece; o soquete é o que ele precisa. Exemplo: o AgenteDeManejo precisa de 5 interfaces e oferece só a IRecomendacao.
3. **DDD.** O core é o diferencial (o agente que decide o manejo). Support alimenta o core, generic é o que todo sistema tem, e infra isola o banco e o que compramos. Cada componente aponta para a EAP e o Gantt dos módulos 2 e 3.
4. **Diagrama de Implantação.** 2 clientes (PC e celular no campo) e 3 servidores no Render (aplicação, rotina e banco), ligados a 3 serviços externos. Os selos AQ-xx são os itens do Quadro de Aquisições.
5. **Nós e artefatos.** O que roda em cada nó e por qual protocolo os nós conversam.
6. **Do diagrama ao código.** Interface vira `Protocol`; soquete vira parâmetro do construtor; nó vira dataclass. As duas funções `conferir_*` provam que os dois diagramas batem entre si.
7. **Componentes em código.** A montagem em `montar_sistema()` são os conectores do diagrama.
8. **Implantação em código.** Os nós no Python e o mesmo desenho no `render.yaml`.
9. **Saída do teste.** Destacar as linhas [R3], [R6] e [R7]: os riscos aparecendo e sendo tratados.
10. **Riscos.** Respostas do registro de riscos que agora estão no código.
11. **Aquisições.** Cada AQ tem um lugar nos diagramas. Fazemos o core e compramos o resto, sempre atrás de uma interface.
12. **Software de gestão.** Cada cartão do Trello corresponde a componentes do diagrama.
13. **Resumo.**
