.PHONY: meshmaker trellis2 hunyuan3d hunyuan3d-part mia hymotion clean

meshmaker: ## Package the MeshMaker Blender addon as meshmaker.zip
	rm -f meshmaker.zip
	zip -r meshmaker.zip meshmaker/ -x 'meshmaker/__pycache__/*' 'meshmaker/*/__pycache__/*'
	@echo "Created meshmaker.zip — install via Blender Preferences → Add-ons → Install"

trellis2: ## Build Trellis 2 Docker image locally
	docker build -t trellis2 containers/trellis2/
	@echo "Built trellis2 image — deploy via GitHub Actions or push manually"

hunyuan3d: ## Build Hunyuan3D 2.1 Docker image locally
	docker build -t hunyuan3d containers/hunyuan3d/
	@echo "Built hunyuan3d image — deploy via GitHub Actions or push manually"

hunyuan3d-part: ## Build Hunyuan3D-Part Docker image locally
	docker build -t hunyuan3d-part containers/hunyuan3d-part/
	@echo "Built hunyuan3d-part image — deploy via GitHub Actions or push manually"

mia: ## Build MIA Docker image locally
	docker build -t mia containers/mia/
	@echo "Built mia image — deploy via GitHub Actions or push manually"

hymotion: ## Build HY-Motion Docker image locally
	docker build -t hymotion containers/hymotion/
	@echo "Built hymotion image — deploy via GitHub Actions or push manually"

clean: ## Remove build artifacts
	rm -f meshmaker.zip
