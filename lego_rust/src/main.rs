use thirtyfour::prelude::*;
use tokio;

async fn go_to_product(driver: &WebDriver, subpath: &str) -> WebDriverResult<()> {
    let base_url = "https://www.lego.com/pl-pl/service/replacement-parts/broken";

    // Ensure exactly one slash between base and subpath, then append suffix
    let full_url = format!(
        "{}/{}{}",
        base_url.trim_end_matches('/'),
        subpath.trim_start_matches('/').trim_end_matches('/'),
        "/pieces?search=*"
    );

    driver.goto(full_url).await?;
    Ok(())
}

#[tokio::main]
async fn main() -> WebDriverResult<()> {
    // Configure Chromium binary path
    let mut caps = DesiredCapabilities::chrome();
    caps.add_chrome_arg("--no-sandbox")?;
    caps.add_chrome_arg("--disable-dev-shm-usage")?;
    caps.add_chrome_arg("--disable-gpu")?;
    caps.add_chrome_arg("--headless=new")?;
    caps.add_chrome_binary("/usr/bin/chromium")?;

    // Connect to Selenium (or chromedriver) running locally
    let driver = WebDriver::new("http://localhost:4444/wd/hub", caps).await?;

    // Example: go to a specific LEGO product page
    go_to_product(&driver, "12345").await?;

    // Keep browser open for a moment (optional)
    tokio::time::sleep(std::time::Duration::from_secs(3)).await;

    driver.quit().await?;
    Ok(())
}
