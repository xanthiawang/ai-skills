import json
import sys
import argparse
from idea_forge.anchors import load_anchors
from idea_forge.retrodiction import retrodiction_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", default="anchors/anchors.yaml")
    ap.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args()
    predicted = json.load(sys.stdin)
    actual = {a.id: a.known_tier for a in load_anchors(args.anchors)}
    rep = retrodiction_report(predicted, actual, args.threshold)
    print(json.dumps({"correlation": round(rep.correlation, 3),
                      "ci": [round(rep.ci_low, 3), round(rep.ci_high, 3)],
                      "n": rep.n, "advisory": rep.advisory, "passed": rep.passed}, indent=2))
    sys.exit(0 if rep.passed else 1)


if __name__ == "__main__":
    main()
