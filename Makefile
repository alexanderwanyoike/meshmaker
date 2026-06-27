.PHONY: meshmaker clean

meshmaker: ## Package the MeshMaker Blender addon as meshmaker.zip
	rm -f meshmaker.zip
	zip -r meshmaker.zip meshmaker/ -x 'meshmaker/__pycache__/*' 'meshmaker/*/__pycache__/*'
	@echo "Created meshmaker.zip - install via Blender Preferences > Add-ons > Install"

clean: ## Remove build artifacts
	rm -f meshmaker.zip
