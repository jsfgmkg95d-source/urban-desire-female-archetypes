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
Assert-True ($archetypes.schema_version -eq '1.1.0') 'schema_version must be 1.1.0'

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

    $cardFile = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'characters') -Filter "$($record.card_id)_*.md" -File -Recurse
    Assert-True ($cardFile.Count -eq 1) "Expected exactly one card file for $($record.card_id)"
    $cardText = Read-Utf8Strict $cardFile.FullName
    foreach ($layer in @('F', 'V', 'M', 'P', 'H', 'X', 'S', 'A')) {
        Assert-True ($cardText -match "(?m)^# $layer =") "Missing layer $layer in $($record.card_id)"
    }
    Assert-True ($cardText -match '(?m)^## H4\. 明确成年现代都市视觉移植$') "Missing H4 in $($record.card_id)"
    Assert-True ($cardText -match '`adaptation_adult_status` \| `DESIGNATED_ADULT`') "H4 status missing in $($record.card_id)"
    Assert-True ($cardText -match '是否把 H4 设计倒填为原著事实：`NO`') "H4 reverse-pollution gate failed in $($record.card_id)"
    foreach ($stage in @('长期匮乏','诱因','第一次越界','即时奖励','自我合理化','风险提高','继续加码','最终代价')) {
        Assert-True ($cardText -match "(?m)^\| $stage \|") "Missing M stage $stage in $($record.card_id)"
    }
    $goldRows = [regex]::Matches($cardText, '(?m)^\| (?:[1-9]|1[0-2]) \|').Count
    Assert-True ($goldRows -eq 12) "Gold questions must have 12 rows in $($record.card_id); got $goldRows"

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

Write-Output "VALIDATION PASSED: $($records.Count) cards; JSON/JSONL, schema, source traceability, H4, M, P, Gold, nearest-neighbor, Markdown links, and UTF-8 checks passed."
