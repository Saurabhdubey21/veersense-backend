import joblib

artifact = joblib.load("./ml/stress_model.pkl")

print("Artifact keys:", list(artifact.keys()))
print()
print("Stored 'features' list:", artifact.get("features"))
print()

model = artifact["model"]
print("Model type:", type(model))

if hasattr(model, "feature_names_in_"):
    print("model.feature_names_in_:", list(model.feature_names_in_))

if hasattr(model, "steps"):
    for name, step in model.steps:
        if hasattr(step, "feature_names_in_"):
            print(f"Step '{name}'.feature_names_in_:", list(step.feature_names_in_))