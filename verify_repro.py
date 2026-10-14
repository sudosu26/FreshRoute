"""Check that optimizer plans are deterministic and include the scenario seed."""

from backend.optimizer import plan_hash, run_optimized
from backend.scenario_generator import generate_scenario


def hash_for_seed(seed: int) -> str:
    scenario = generate_scenario(seed=seed)
    plan, _ = run_optimized(
        scenario["batches"],
        scenario["destinations"],
        scenario["trucks"],
    )
    return plan_hash(plan, seed)


def main() -> int:
    try:
        first = hash_for_seed(12345)
        repeated = hash_for_seed(12345)
        different = hash_for_seed(12346)
        if first != repeated:
            raise AssertionError("same seed produced different plan hashes")
        if first == different:
            raise AssertionError("different seed produced the same plan hash")
    except (AssertionError, TypeError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: same seed reproduces the plan hash; different seed changes it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
