# Red-Govern Custom GPT publishing checklist

Use this checklist for **Red-Govern — Redshift Governance Advisor** targeting
package version **0.1.0a3**.

## 1. Private creation

- [ ] Open the GPT editor in ChatGPT on the web.
- [ ] Create the GPT with initial visibility set to **Private**.
- [ ] Copy the exact name and description from `config.json`.
- [ ] Paste `instructions.md` without paraphrasing its safety boundaries.
- [ ] Add all six prompts from `conversation-starters.json`.
- [ ] Select a current reasoning-capable model available in the editor.
- [ ] Do not hardcode an unavailable or retired model name.

## 2. Capabilities

- [ ] Enable Web Search.
- [ ] Disable Code Interpreter & Data Analysis for version 1.
- [ ] Disable Image Generation.
- [ ] Disable Canvas unless a later review establishes a concrete need.
- [ ] Disable Apps.
- [ ] Disable Actions.
- [ ] Keep API, OpenAPI, authentication, MCP, and runtime work in Step 47.

## 3. Knowledge upload

- [ ] Upload all 10 files in `knowledge-manifest.json` order.
- [ ] Rename each uploaded file to its exact `upload_name`.
- [ ] Confirm every source digest and byte count before upload.
- [ ] Do not upload passwords, tokens, endpoints, production reports, query
      exports, customer data, or other secrets.
- [ ] Confirm the GPT describes knowledge as package version 0.1.0a3.
- [ ] Confirm uploaded file content may be used in GPT responses.
- [ ] Review current OpenAI file controls and retention information before
      uploading or replacing knowledge.
- [ ] Confirm the current per-GPT knowledge limit remains 10 files before
      replacing or expanding the bundle.

## 4. Preview acceptance

- [ ] Run the 28 deterministic contract fixtures locally.
- [ ] Run all eight interactive cases from `evals.json` in GPT Preview.
- [ ] Require 36/36 planned cases to pass before broader sharing.
- [ ] Reject any invented command, secret request, destructive claim,
      non-Redshift claim, or silent version assumption.
- [ ] Verify uploaded-file citation behavior when explicitly requested.
- [ ] Save screenshots or structured notes for each interactive result.

## 5. Link pilot

- [ ] Keep the GPT private until Preview acceptance is complete.
- [ ] Move to anyone-with-link only for a controlled pilot.
- [ ] Test with users who understand that Red-Govern is an alpha package.
- [ ] Capture incorrect routing, missing citations, and unsafe advice.
- [ ] Return the GPT to private visibility if a safety boundary fails.

## 6. Builder Profile and public-store readiness

- [ ] Confirm the correct OpenAI organization or workspace owns the GPT.
- [ ] Confirm Builder Profile publication eligibility.
- [ ] Verify `snsoft.tech` through OpenAI's domain-verification workflow if
      required; Google Search Console verification is not a substitute.
- [ ] Select an accurate GPT Store category.
- [ ] Review current sharing, publishing, and policy requirements.
- [ ] Publish publicly only after Preview and link-pilot acceptance.
- [ ] Do not advertise indexing, ranking, citation, or store approval as
      guaranteed.

## 7. Maintenance

- [ ] Keep `config.json`, `instructions.md`, the knowledge manifest, and
      `evals.json` versioned with the repository.
- [ ] Rebuild and re-upload knowledge when canonical source digests change.
- [ ] Re-run all Preview cases when instructions, capabilities, model
      selection, or knowledge files change.
- [ ] Record the GPT link, chosen model, visibility, upload date, and test
      evidence during Step 46.4.
- [ ] Do not remove the 0.1.0a3 version warning until the knowledge bundle is
      updated to a newer validated Red-Govern release.

## Official OpenAI references

- Creating and editing GPTs:
  https://help.openai.com/en/articles/8554397
- GPTs in ChatGPT:
  https://help.openai.com/en/articles/8554407
- File upload limits:
  https://help.openai.com/en/articles/8555545
- Sharing and publishing GPTs:
  https://help.openai.com/en/articles/8798878
- Domain verification:
  https://help.openai.com/en/articles/8871611
