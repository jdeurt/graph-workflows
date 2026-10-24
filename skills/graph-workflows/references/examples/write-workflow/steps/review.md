# Review the candidate

Given Requirements, Standard, Design, and Candidate files, compare the candidate with the requested behavior and format. Read each node using only its declared inputs. Check that decisions are understandable and mutually exclusive, failures are recoverable or reported, nested workflows return the required outputs, and all paths can complete as intended.

Check Markdown references and any concurrency instructions, including input ownership, complete result collection, and capability fallback. Identify prose that depends on another node's hidden history. Do not claim that static graph checks prove natural-language conditions or semantic self-containment.

Return Review findings with file locations and concrete corrections, or an empty list when no issues remain. Return the supplied artifacts unchanged to the caller.
