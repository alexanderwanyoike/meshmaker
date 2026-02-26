.PHONY: addon rigmaker animmaker mia clean

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

animmaker: ## Package the AnimMaker addon as animmaker.zip
	rm -f animmaker.zip
	zip -r animmaker.zip animmaker/ -x 'animmaker/__pycache__/*'
	@echo "Created animmaker.zip — install via Blender Preferences → Add-ons → Install"

mia: ## Build MIA Docker image locally
	docker build -t mia containers/mia/
	@echo "Built mia image — deploy via GitHub Actions or push manually"

clean: ## Remove build artifacts
	rm -f charmaker.zip rigmaker.zip animmaker.zip
