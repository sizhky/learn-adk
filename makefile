create-agent:
	@if [ "$(word 2,$(MAKECMDGOALS))" = "" ]; then \
		echo "Usage: make create-agent AGENT_NAME"; \
		exit 1; \
	fi
	@AGENT_NAME=$(word 2,$(MAKECMDGOALS)) && \
	mkdir -p $$AGENT_NAME && \
	touch $$AGENT_NAME/agent.py $$AGENT_NAME/__init__.py && \
	echo "from . import agent" > $$AGENT_NAME/__init__.py && \
	echo "Created agent with name: $$AGENT_NAME"

.PHONY: create-agent

%:
	@: