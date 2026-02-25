.PHONY: addon rigmaker clean

addon: ## Package the Blender addon as charmaker.zip
	rm -f charmaker.zip
	ln -sfn addon charmaker
	zip -r charmaker.zip charmaker/ -x 'charmaker/__pycache__/*'
	rm charmaker
	@echo "Created charmaker.zip — install via Blender Preferences → Add-ons → Install"

rigmaker: ## Package the RigMaker addon as rigmaker.zip
	rm -f rigmaker.zip
	zip -r rigmaker.zip rigmaker/ -x 'rigmaker/__pycache__/*'
	@echo "Created rigmaker.zip — install via Blender Preferences → Add-ons → Install"

clean: ## Remove build artifacts
	rm -f charmaker.zip rigmaker.zip
