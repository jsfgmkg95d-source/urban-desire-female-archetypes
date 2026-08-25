[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$utf8Strict = [System.Text.UTF8Encoding]::new($false, $true)

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Read-Utf8Strict {
    param([string]$Path)
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -ge 3) {
        Assert-True -Condition (-not ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)) -Message "UTF-8 BOM is not allowed: $Path"
    }
    return $utf8Strict.GetString($bytes)
}

$archetypePath = Join-Path $repoRoot 'data/archetypes.json'
$archetypes = Read-Utf8Strict $archetypePath | ConvertFrom-Json
Assert-True ($archetypes.schema_version -eq '1.2.0') 'schema_version must be 1.2.0'

$validArchetypes = @($archetypes.archetypes.id)
$validAdult = @($archetypes.enums.adult_status)
$validFunctions = @($archetypes.enums.visual_plot_function)
$requiredMachineFields = @($archetypes.record_contract.machine_retrieval_fields)
$scoreDimensions = @($archetypes.score_dimensions)

$jsonlPath = Join-Path $repoRoot 'data/characters.jsonl'
$jsonlText = Read-Utf8Strict $jsonlPath
$records = @($jsonlText -split "`r?`n" | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
Assert-True ($records.Count -ge 2) 'At least two calibrated records are required'
Assert-True ((@($records.card_id | Sort-Object -Unique)).Count -eq $records.Count) 'Duplicate card_id in characters.jsonl'
Assert-True ($records.Count -eq 10) 'Batch 001 must contain exactly ten production records'
Assert-True ((@($archetypes.character_records.card_id | Sort-Object -Unique)).Count -eq $records.Count) 'archetypes.json character_records count mismatch'
foreach ($recordId in $records.card_id) {
    Assert-True ($archetypes.character_records.card_id -contains $recordId) "Missing character_records entry for $recordId"
}

foreach ($record in $records) {
    foreach ($field in $requiredMachineFields) {
        Assert-True ($null -ne $record.PSObject.Properties[$field]) "Missing machine field $field in $($record.card_id)"
    }
    Assert-True ($validAdult -contains $record.adult_status) "Invalid adult_status in $($record.card_id)"
    Assert-True ($validArchetypes -contains $record.primary_archetype_id) "Invalid primary archetype in $($record.card_id)"
    foreach ($secondary in $record.secondary_archetype_ids) {
        Assert-True ($validArchetypes -contains $secondary) "Invalid secondary archetype $secondary in $($record.card_id)"
    }
    Assert-True ($record.secondary_archetype_ids.Count -le $archetypes.constraints.secondary_archetypes_max) "Too many secondary archetypes in $($record.card_id)"
    Assert-True ($record.adult_adaptation_age -ge $archetypes.constraints.adult_adaptation_age_min) "H4 age gate failed in $($record.card_id)"
    Assert-True ($record.adult_visual_signature.Count -ge $archetypes.constraints.adult_adaptation_visual_signature_min) "H4 visual signature too short in $($record.card_id)"
    Assert-True ($record.adult_visual_signature.Count -le $archetypes.constraints.adult_adaptation_visual_signature_max) "H4 visual signature too long in $($record.card_id)"
    foreach ($fn in $record.adult_visual_plot_functions) {
        Assert-True ($validFunctions -contains $fn) "Invalid H4 plot function $fn in $($record.card_id)"
    }
    foreach ($dimension in $scoreDimensions) {
        $value = $record.scores.$dimension
        Assert-True ($null -ne $value) "Missing score $dimension in $($record.card_id)"
        Assert-True ($value -ge 0 -and $value -le 5) "Score out of range: $dimension in $($record.card_id)"
    }
    Assert-True ($record.scores.evidence_confidence -ge 0 -and $record.scores.evidence_confidence -le 3) "Evidence confidence out of range in $($record.card_id)"
    Assert-True ($record.plot_engine_ids.Count -ge $archetypes.constraints.gold_plot_engines_min) "Gold plot engines missing in $($record.card_id)"
    Assert-True ($record.nearest_neighbor_card_id -and $record.nearest_neighbor_card_id -ne $record.card_id) "Invalid nearest neighbor in $($record.card_id)"
    Assert-True ($records.card_id -contains $record.nearest_neighbor_card_id) "Nearest neighbor does not exist in $($record.card_id)"
    Assert-True ($record.anti_clone_result -eq 'PASS') "Anti-Clone not passed in $($record.card_id)"
    Assert-True ($record.schema_version -eq $archetypes.schema_version) "Record schema mismatch in $($record.card_id)"
    Assert-True ($record.layer_completion.R -eq $true) "R layer incomplete in $($record.card_id)"
    Assert-True ($record.retrieval_capsule.one_line_archetype.Length -le $archetypes.constraints.retrieval_one_line_max_chars) "R1 exceeds 40 characters in $($record.card_id)"
    Assert-True ($record.retrieval_capsule.visual_signature.memory_points.Count -ge 1 -and $record.retrieval_capsule.visual_signature.memory_points.Count -le 3) "R2 memory points invalid in $($record.card_id)"
    Assert-True ($record.retrieval_capsule.forbidden_as.Count -eq $archetypes.constraints.retrieval_forbidden_as_required) "R7 must have exactly three items in $($record.card_id)"
    Assert-True (-not [string]::IsNullOrWhiteSpace($record.retrieval_capsule.machine_call_string)) "R8 missing in $($record.card_id)"
    Assert-True ($record.archetype_uniqueness_statement.Length -le $archetypes.constraints.gold_uniqueness_statement_max_chars) "Uniqueness statement exceeds 60 characters in $($record.card_id)"
    Assert-True (-not [string]::IsNullOrWhiteSpace($record.archetype_uniqueness_statement)) "Uniqueness statement missing in $($record.card_id)"

    $cardFile = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'characters') -Filter "$($record.card_id)_*.md" -File -Recurse
    Assert-True ($cardFile.Count -eq 1) "Expected exactly one card file for $($record.card_id)"
    $cardText = Read-Utf8Strict $cardFile.FullName
    foreach ($layer in @('F', 'V', 'M', 'P', 'H', 'X', 'S', 'A', 'R')) {
        Assert-True ($cardText -match "(?m)^# $layer =") "Missing layer $layer in $($record.card_id)"
    }
    Assert-True ($cardText -match '(?m)^## H4\. 明确成年现代都市视觉移植$') "Missing H4 in $($record.card_id)"
    Assert-True ($cardText -match '`adaptation_adult_status` \| `DESIGNATED_ADULT`') "H4 status missing in $($record.card_id)"
    Assert-True ($cardText -match '是否把 H4 设计倒填为原著事实：`NO`') "H4 reverse-pollution gate failed in $($record.card_id)"
    if ($record.adult_status -eq 'UNKNOWN') {
        Assert-True ($cardText -match '允许直白身体分析：`NO`') "UNKNOWN adult original V must be closed in $($record.card_id)"
        Assert-True ($cardText -match '低俗第一眼：`NOT_APPLICABLE：年龄门未通过`') "UNKNOWN adult original first glance must be NOT_APPLICABLE in $($record.card_id)"
    }
    foreach ($stage in @('长期匮乏','诱因','第一次越界','即时奖励','自我合理化','风险提高','继续加码','最终代价')) {
        Assert-True ($cardText -match "(?m)^\| $stage \|") "Missing M stage $stage in $($record.card_id)"
    }
    $goldRows = [regex]::Matches($cardText, '(?m)^\| (?:[1-9]|1[0-2]) \|').Count
    Assert-True ($goldRows -eq 12) "Gold questions must have 12 rows in $($record.card_id); got $goldRows"
    Assert-True ($cardText -match '(?m)^# 母体唯一性声明') "Missing uniqueness statement in $($record.card_id)"
    foreach ($rSection in 1..8) {
        Assert-True ($cardText -match "(?m)^## R$rSection\.") "Missing R$rSection in $($record.card_id)"
    }

    $sourceFile = Join-Path $repoRoot "sources/$($record.card_id)_sources.md"
    Assert-True (Test-Path -LiteralPath $sourceFile) "Missing source file for $($record.card_id)"
    $sourceText = Read-Utf8Strict $sourceFile
    foreach ($sourceId in $record.source_ids) {
        Assert-True ($sourceText.Contains($sourceId)) "Untraceable source_id $sourceId in $($record.card_id)"
    }
    foreach ($line in ($cardText -split "`r?`n" | Where-Object { $_ -match '^\| `F-(?:VIS|REL|ACT|RES|COMP|SEC|OUT|RISK|\d)' })) {
        Assert-True ($line -match "$($record.card_id)-S\d{2}:" ) "F fact lacks source locator in $($record.card_id): $line"
    }
}

$primaryVisualFocus = @($records | ForEach-Object { $_.retrieval_capsule.visual_signature.memory_points[0] })
$largestExactFocusGroup = @($primaryVisualFocus | Group-Object | Sort-Object Count -Descending | Select-Object -First 1)[0]
Assert-True ($largestExactFocusGroup.Count -le 3) "Visual 30 percent rule failed for exact focus $($largestExactFocusGroup.Name)"
Assert-True ((@($records.adult_adaptation_role | Sort-Object -Unique)).Count -ge 8) 'Occupation distribution is too concentrated'

$requiredIndexes = @(
    'master-index.md',
    'by-archetype.md',
    'by-visual-hook.md',
    'by-identity.md',
    'by-desire-mechanism.md',
    'by-power-method.md',
    'by-secret-method.md',
    'by-modern-role.md',
    'by-plot-engine.md'
)
foreach ($indexName in $requiredIndexes) {
    Assert-True (Test-Path -LiteralPath (Join-Path $repoRoot "indexes/$indexName")) "Missing required index $indexName"
}
$batchAuditPath = Join-Path $repoRoot 'batches/batch-001-ten-gold-candidates.md'
Assert-True (Test-Path -LiteralPath $batchAuditPath) 'Missing ten-card global audit'
$batchAuditText = Read-Utf8Strict $batchAuditPath
foreach ($pair in @('Pair A','Pair B','Pair C','Pair D')) {
    Assert-True ($batchAuditText.Contains($pair)) "Missing $pair audit"
}
Assert-True ($batchAuditText.Contains('visual_30_percent_rule`：`PASS')) 'Batch visual distribution audit not passed'
Assert-True ($batchAuditText.Contains('occupation_distribution`：`PASS')) 'Batch occupation distribution audit not passed'

$markdownFiles = Get-ChildItem -LiteralPath $repoRoot -Filter '*.md' -File -Recurse | Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' }
foreach ($file in $markdownFiles) {
    $text = Read-Utf8Strict $file.FullName
    foreach ($match in [regex]::Matches($text, '\]\(([^)]+)\)')) {
        $target = $match.Groups[1].Value
        if ($target -match '^(?:https?://|#)') { continue }
        $targetPath = [System.IO.Path]::GetFullPath((Join-Path $file.DirectoryName $target))
        Assert-True (Test-Path -LiteralPath $targetPath) "Broken Markdown link in $($file.FullName): $target"
    }
}

Write-Output "VALIDATION PASSED: $($records.Count) cards; JSON/JSONL, schema, source traceability, H4, M, P, Gold, R, uniqueness, nearest-neighbor, Markdown links, and UTF-8 checks passed."
