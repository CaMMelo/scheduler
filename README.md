# SCHEDULER

ferramenta para organização automatica de tarefas

* Defina tarefas recorrentes em cronogramas semanais,
* Defina projetos, adicionando as tarefas necessarias para finalizar o projeto, e o prazo do projeto
* Habilite os cronogramas semanais necessarios
* Selecione os projetos que seão realizados manualmente, ou faça uma seleção automatica
* Escolha os horarios em que cada projeto será executado, manual ou automatizadamente

---

## Basics

O Scheduler é dividido nos seguintes conceitos:

* Cronograma (schedule)

	Um cronograma organiza tarefas por horario de execução,
	cada cronograma está relacionado à uma data especifica,
	assim é possível saber o que foi ou será feito em uma
	determinada data.

* Cronograma Semanal (weekly_schedule)

	Um cronograma semanal organiza tarefas por horario de execução
	e por dia da semana, sendo possivel saber sobre habitos realizados
	metodicamente pelo usuario.
	É possivel criar diversos cronogramas semanais, assim é possivel
	declarar as tarefas relacinadas a um aspecto especifico do dia-a-dia
	do usuario.
	Os cronogramas semanais devem ser habilitados / desabilitados, entre
	datas especificas.

* Tarefa Escalonavel (scalable_task)

	Uma tarefa escalonavel possui um horario de inicio e de termino,
	essas tarefas são usadas em cronogramas para indicar o que será
	feito em um determinado espaço de tempo.

* Projeto

	Um projeto é um conjunto de tarefas que têm de ser realizadas até
	um determinado prazo.
	Cada projeto possui um determinado numero de "estrelas", para indicar
	o nivel de importancia do projeto.
	Um projeto deve ser selecionado para escalonamento, e não pode ser
	modificado a partir de entao.

* Tarefa de Projeto (project_task)
	
	Uma tarefa de projeto é utilizada para indicar algo que deve
	ser feito para a conclusão de um projeto.
	Cada tarefa desse tipo possui uma duração em minutos, e um
	marcador de conclusão (indicando se essa tarefa foi ou não concluida)