$POD = "maps-backend-767b4cc874-7mgm5"
$NS = "maps-python"

Write-Host "Copying metadata.json..."
kubectl cp "library\metadata.json" "${NS}/${POD}:/app/library/metadata.json"

Write-Host "Copying image files..."
Get-ChildItem "library\images\*" | ForEach-Object {
    Write-Host "  Copying $($_.Name)..."
    kubectl cp $_.FullName "${NS}/${POD}:/app/library/images/$($_.Name)"
}

Write-Host "Done! Verifying..."
kubectl exec -n $NS $POD -- ls -lh /app/library/images/
