# Módulo 4 · o que entregar e como apresentar

## Anexar no Classroom

- `Módulo4.pdf`: o pitch (12 slides)
- `main.py`: o snippet corrigido (roda com `python main.py`)
- `saida-do-teste.txt`: a saída do `main.py`
- `diagramas/`: Diagrama de Sequência e Diagrama de Estados em PNG

O `main.py` original, feito às pressas, continua em `modulo-4/original/main.py`. A versão da entrega é a de `entrega/`: o bug foi corrigido e o código ficou mais próximo do DS.

## O que mudou no snippet

- **Bug corrigido:** a versão original aceitava quantidade negativa (adicionar −5 bois deixava a lotação em −5). Agora `validar_quantidades()` rejeita quantidade negativa, fracionada e categoria desconhecida.
- **Métodos novos:** mais mensagens do DS ganharam método próprio (`validar_quantidades`, `listar_piquetes`, `salvar_leitura_ndvi`, `buscar_lotacao`, `montar_prompt`), e o banco virou o participante `BancoDeDados`.
- **Transições do DE:** viraram a tabela `TRANSICOES_NDVI`. Seta que não existe no diagrama é recusada.
- **Critérios de qualidade:** `verificar_criterios_de_qualidade()` testa os critérios 3.1, 3.2 e 2.2.1 da Gestão de Qualidade (9/9 passam).

## Roteiro do pitch

1. **Capa.**
2. **e 3. Diagrama de Sequência:** cadastro e movimentação; depois a rotina agendada e a consulta.
4. **Diagrama de Estados:** duas regiões ao mesmo tempo, a ocupação e o NDVI.
5. **e 6. Diagramas no código:** cada trecho do DS e cada seta do DE e onde estão no código.
7. **Trechos do código.**
8. **Saída do teste:** destacar as 9 verificações.
9. **Qualidade:** os critérios viraram teste, e o teste achou um defeito de severidade 1.
10. **RH:** quem cuida de cada participante do DS. O back-end está sobrecarregado (risco R1), então a validação vai para o front.
11. **Comunicações:** cada seta entre papéis é um acordo; quando muda, quem avisa quem.
12. **Resumo.**
