/**
 * Certificate Installer - Client-side JavaScript
 * Handles device detection, download tracking, and UI interactions
 */

(function() {
    'use strict';

    // ========================================
    // Device Detection
    // ========================================

    const DeviceDetector = {
        /**
         * Get detailed device information
         */
        getDeviceInfo: function() {
            const ua = navigator.userAgent;
            const platform = navigator.platform;
            
            return {
                userAgent: ua,
                platform: platform,
                device: this.detectDevice(ua),
                os: this.detectOS(ua, platform),
                browser: this.detectBrowser(ua),
                isMobile: this.isMobile(ua),
                isTablet: this.isTablet(ua),
                screenWidth: window.screen.width,
                screenHeight: window.screen.height
            };
        },

        /**
         * Detect device type
         */
        detectDevice: function(ua) {
            if (/iPhone/i.test(ua)) return 'iPhone';
            if (/iPad/i.test(ua)) return 'iPad';
            if (/iPod/i.test(ua)) return 'iPod';
            if (/Android/i.test(ua)) {
                if (/Mobile/i.test(ua)) return 'Android Phone';
                return 'Android Tablet';
            }
            if (/Windows Phone/i.test(ua)) return 'Windows Phone';
            if (/Macintosh/i.test(ua)) return 'Mac';
            if (/Windows/i.test(ua)) return 'Windows PC';
            if (/Linux/i.test(ua)) return 'Linux PC';
            if (/CrOS/i.test(ua)) return 'Chromebook';
            return 'Unknown';
        },

        /**
         * Detect operating system and version
         */
        detectOS: function(ua, platform) {
            // iOS
            const iosMatch = ua.match(/OS (\d+)_(\d+)_?(\d+)?/);
            if (iosMatch) {
                return {
                    name: 'iOS',
                    version: `${iosMatch[1]}.${iosMatch[2]}${iosMatch[3] ? '.' + iosMatch[3] : ''}`,
                    majorVersion: parseInt(iosMatch[1])
                };
            }

            // Android
            const androidMatch = ua.match(/Android (\d+)\.?(\d+)?\.?(\d+)?/);
            if (androidMatch) {
                return {
                    name: 'Android',
                    version: `${androidMatch[1]}${androidMatch[2] ? '.' + androidMatch[2] : ''}`,
                    majorVersion: parseInt(androidMatch[1])
                };
            }

            // Windows
            if (/Windows NT 10/i.test(ua)) {
                return { name: 'Windows', version: '10/11', majorVersion: 10 };
            }
            if (/Windows NT 6.3/i.test(ua)) {
                return { name: 'Windows', version: '8.1', majorVersion: 8 };
            }
            if (/Windows NT 6.2/i.test(ua)) {
                return { name: 'Windows', version: '8', majorVersion: 8 };
            }
            if (/Windows NT 6.1/i.test(ua)) {
                return { name: 'Windows', version: '7', majorVersion: 7 };
            }

            // macOS
            const macMatch = ua.match(/Mac OS X (\d+)[_.](\d+)/);
            if (macMatch) {
                return {
                    name: 'macOS',
                    version: `${macMatch[1]}.${macMatch[2]}`,
                    majorVersion: parseInt(macMatch[1])
                };
            }

            // Chrome OS
            if (/CrOS/i.test(ua)) {
                const crosMatch = ua.match(/CrOS \w+ (\d+)/);
                return {
                    name: 'Chrome OS',
                    version: crosMatch ? crosMatch[1] : 'Unknown',
                    majorVersion: crosMatch ? parseInt(crosMatch[1]) : 0
                };
            }

            // Linux
            if (/Linux/i.test(ua) && !/Android/i.test(ua)) {
                return { name: 'Linux', version: 'Unknown', majorVersion: 0 };
            }

            return { name: 'Unknown', version: 'Unknown', majorVersion: 0 };
        },

        /**
         * Detect browser
         */
        detectBrowser: function(ua) {
            if (/Edge/i.test(ua) || /Edg\//i.test(ua)) return 'Edge';
            if (/Chrome/i.test(ua) && !/Chromium/i.test(ua)) return 'Chrome';
            if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) return 'Safari';
            if (/Firefox/i.test(ua)) return 'Firefox';
            if (/Opera|OPR/i.test(ua)) return 'Opera';
            if (/MSIE|Trident/i.test(ua)) return 'Internet Explorer';
            return 'Unknown';
        },

        /**
         * Check if mobile device
         */
        isMobile: function(ua) {
            return /Mobile|Android|iPhone|iPod|Windows Phone/i.test(ua);
        },

        /**
         * Check if tablet
         */
        isTablet: function(ua) {
            return /iPad|Android(?!.*Mobile)/i.test(ua);
        }
    };

    // ========================================
    // Download Tracking
    // ========================================

    const DownloadTracker = {
        /**
         * Track certificate download
         */
        trackDownload: function(deviceType) {
            // Send tracking data to server
            fetch('/api/track-download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device: deviceType,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent,
                    screenSize: `${window.screen.width}x${window.screen.height}`
                })
            }).catch(function(err) {
                console.log('Tracking failed:', err);
            });
        },

        /**
         * Track step completion
         */
        trackStep: function(step, deviceType) {
            fetch('/api/track-step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    step: step,
                    device: deviceType,
                    timestamp: new Date().toISOString()
                })
            }).catch(function(err) {
                console.log('Step tracking failed:', err);
            });
        },

        /**
         * Track installation completion
         */
        trackComplete: function(deviceType) {
            fetch('/api/track-complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device: deviceType,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                })
            }).catch(function(err) {
                console.log('Completion tracking failed:', err);
            });
        }
    };

    // ========================================
    // UI Helpers
    // ========================================

    const UI = {
        /**
         * Show a toast notification
         */
        showToast: function(message, type) {
            type = type || 'info';
            
            // Remove existing toast
            const existing = document.querySelector('.toast');
            if (existing) {
                existing.remove();
            }

            // Create toast element
            const toast = document.createElement('div');
            toast.className = 'toast toast-' + type;
            toast.textContent = message;

            // Style the toast
            Object.assign(toast.style, {
                position: 'fixed',
                bottom: '20px',
                left: '50%',
                transform: 'translateX(-50%)',
                padding: '12px 24px',
                borderRadius: '8px',
                color: 'white',
                fontWeight: '500',
                zIndex: '10000',
                animation: 'fadeIn 0.3s ease'
            });

            // Set background based on type
            const colors = {
                success: '#10b981',
                error: '#ef4444',
                warning: '#f59e0b',
                info: '#3b82f6'
            };
            toast.style.backgroundColor = colors[type] || colors.info;

            document.body.appendChild(toast);

            // Auto-remove after 3 seconds
            setTimeout(function() {
                toast.style.animation = 'fadeOut 0.3s ease';
                setTimeout(function() {
                    toast.remove();
                }, 300);
            }, 3000);
        },

        /**
         * Update progress bar
         */
        updateProgress: function(current, total) {
            const progressBar = document.querySelector('.progress-fill');
            const progressText = document.querySelector('.progress-text');
            
            if (progressBar) {
                const percentage = (current / total) * 100;
                progressBar.style.width = percentage + '%';
            }
            
            if (progressText) {
                progressText.textContent = 'Step ' + current + ' of ' + total;
            }
        },

        /**
         * Show/hide loading spinner
         */
        setLoading: function(isLoading) {
            let spinner = document.querySelector('.loading-spinner');
            
            if (isLoading) {
                if (!spinner) {
                    spinner = document.createElement('div');
                    spinner.className = 'loading-spinner';
                    spinner.innerHTML = '<div class="spinner"></div>';
                    Object.assign(spinner.style, {
                        position: 'fixed',
                        top: '0',
                        left: '0',
                        width: '100%',
                        height: '100%',
                        backgroundColor: 'rgba(0,0,0,0.5)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: '9999'
                    });
                    document.body.appendChild(spinner);
                }
            } else if (spinner) {
                spinner.remove();
            }
        },

        /**
         * Highlight active step
         */
        highlightStep: function(stepNumber) {
            const steps = document.querySelectorAll('.step-card');
            steps.forEach(function(step, index) {
                step.classList.remove('active', 'completed');
                if (index < stepNumber - 1) {
                    step.classList.add('completed');
                } else if (index === stepNumber - 1) {
                    step.classList.add('active');
                }
            });
        },

        /**
         * Smooth scroll to element
         */
        scrollTo: function(selector) {
            const element = document.querySelector(selector);
            if (element) {
                element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        },

        /**
         * Copy text to clipboard
         */
        copyToClipboard: function(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(function() {
                    UI.showToast('Copied to clipboard!', 'success');
                }).catch(function() {
                    UI.fallbackCopy(text);
                });
            } else {
                UI.fallbackCopy(text);
            }
        },

        /**
         * Fallback copy method for older browsers
         */
        fallbackCopy: function(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            
            try {
                document.execCommand('copy');
                UI.showToast('Copied to clipboard!', 'success');
            } catch (err) {
                UI.showToast('Failed to copy', 'error');
            }
            
            document.body.removeChild(textarea);
        }
    };

    // ========================================
    // Step Navigation
    // ========================================

    const StepNavigator = {
        currentStep: 1,
        totalSteps: 4,

        /**
         * Initialize step navigation
         */
        init: function() {
            const self = this;
            
            // Get total steps from page
            const steps = document.querySelectorAll('.step-card');
            if (steps.length > 0) {
                this.totalSteps = steps.length;
            }

            // Add click handlers to next buttons
            document.querySelectorAll('[data-next-step]').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    const nextStep = parseInt(this.getAttribute('data-next-step'));
                    self.goToStep(nextStep);
                });
            });

            // Add click handlers to step indicators
            document.querySelectorAll('.step-indicator').forEach(function(indicator, index) {
                indicator.addEventListener('click', function() {
                    if (index + 1 <= self.currentStep) {
                        self.goToStep(index + 1);
                    }
                });
            });

            // Highlight first step
            UI.highlightStep(1);
        },

        /**
         * Go to specific step
         */
        goToStep: function(stepNumber) {
            if (stepNumber < 1 || stepNumber > this.totalSteps) return;

            this.currentStep = stepNumber;
            UI.highlightStep(stepNumber);
            UI.updateProgress(stepNumber, this.totalSteps);
            UI.scrollTo('.step-card:nth-child(' + stepNumber + ')');

            // Track step
            const deviceInfo = DeviceDetector.getDeviceInfo();
            DownloadTracker.trackStep(stepNumber, deviceInfo.os.name);
        },

        /**
         * Mark current step complete and go to next
         */
        completeStep: function() {
            if (this.currentStep < this.totalSteps) {
                this.goToStep(this.currentStep + 1);
            } else {
                // All steps complete
                this.onComplete();
            }
        },

        /**
         * Handle completion
         */
        onComplete: function() {
            const deviceInfo = DeviceDetector.getDeviceInfo();
            DownloadTracker.trackComplete(deviceInfo.os.name);
            
            // Redirect to completion page if not already there
            if (!window.location.pathname.includes('/complete')) {
                window.location.href = '/complete';
            }
        }
    };

    // ========================================
    // Certificate Download Handler
    // ========================================

    const CertDownloader = {
        /**
         * Handle certificate download
         */
        download: function(format) {
            format = format || 'pem';
            
            const deviceInfo = DeviceDetector.getDeviceInfo();
            DownloadTracker.trackDownload(deviceInfo.os.name);

            // Show loading
            UI.setLoading(true);

            // Create download link
            const link = document.createElement('a');
            link.href = '/download/cert.' + format;
            link.download = 'NetworkSecurityCert.' + format;
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Hide loading after short delay
            setTimeout(function() {
                UI.setLoading(false);
                UI.showToast('Certificate downloaded!', 'success');
                
                // Advance to next step if using step navigation
                if (StepNavigator.currentStep === 1) {
                    setTimeout(function() {
                        StepNavigator.completeStep();
                    }, 1000);
                }
            }, 500);
        },

        /**
         * Get appropriate format for device
         */
        getRecommendedFormat: function() {
            const deviceInfo = DeviceDetector.getDeviceInfo();
            const os = deviceInfo.os.name;

            if (os === 'iOS' || os === 'macOS') {
                return 'pem';
            } else if (os === 'Android') {
                return 'der';
            } else if (os === 'Windows') {
                return 'crt';
            }
            return 'pem';
        }
    };

    // ========================================
    // Help & Support
    // ========================================

    const HelpSystem = {
        /**
         * Show help modal
         */
        showHelp: function(topic) {
            const helpContent = this.getHelpContent(topic);
            
            // Create modal
            const modal = document.createElement('div');
            modal.className = 'help-modal';
            modal.innerHTML = `
                <div class="help-modal-overlay"></div>
                <div class="help-modal-content">
                    <button class="help-modal-close">&times;</button>
                    <h3>${helpContent.title}</h3>
                    <div class="help-modal-body">${helpContent.body}</div>
                </div>
            `;

            // Style modal
            Object.assign(modal.style, {
                position: 'fixed',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                zIndex: '10000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            });

            const overlay = modal.querySelector('.help-modal-overlay');
            Object.assign(overlay.style, {
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                backgroundColor: 'rgba(0,0,0,0.5)'
            });

            const content = modal.querySelector('.help-modal-content');
            Object.assign(content.style, {
                position: 'relative',
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '24px',
                maxWidth: '500px',
                maxHeight: '80vh',
                overflow: 'auto',
                margin: '20px'
            });

            const closeBtn = modal.querySelector('.help-modal-close');
            Object.assign(closeBtn.style, {
                position: 'absolute',
                top: '12px',
                right: '12px',
                border: 'none',
                background: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
            });

            document.body.appendChild(modal);

            // Close handlers
            closeBtn.addEventListener('click', function() {
                modal.remove();
            });
            overlay.addEventListener('click', function() {
                modal.remove();
            });
        },

        /**
         * Get help content for topic
         */
        getHelpContent: function(topic) {
            const helpTopics = {
                'why-certificate': {
                    title: 'Why Install a Security Certificate?',
                    body: `
                        <p>Security certificates help protect your network connection by:</p>
                        <ul>
                            <li>Encrypting your data to prevent unauthorized access</li>
                            <li>Verifying the identity of network services</li>
                            <li>Enabling secure connections to protected resources</li>
                        </ul>
                        <p>This certificate is required for optimal network security and performance.</p>
                    `
                },
                'is-it-safe': {
                    title: 'Is This Safe?',
                    body: `
                        <p>Yes, installing this certificate is completely safe:</p>
                        <ul>
                            <li>It's specifically designed for your network</li>
                            <li>It follows industry-standard security practices</li>
                            <li>You can remove it at any time from your device settings</li>
                        </ul>
                    `
                },
                'trouble-downloading': {
                    title: 'Trouble Downloading?',
                    body: `
                        <p>If you're having trouble downloading the certificate:</p>
                        <ol>
                            <li>Make sure you're connected to WiFi</li>
                            <li>Try using a different browser (Chrome or Safari recommended)</li>
                            <li>Check that you have enough storage space</li>
                            <li>Disable any VPN or proxy temporarily</li>
                        </ol>
                    `
                },
                'contact-support': {
                    title: 'Need More Help?',
                    body: `
                        <p>If you're still having issues, please contact your network administrator for assistance.</p>
                        <p>When contacting support, please provide:</p>
                        <ul>
                            <li>Your device type and model</li>
                            <li>Operating system version</li>
                            <li>A description of the issue</li>
                        </ul>
                    `
                }
            };

            return helpTopics[topic] || {
                title: 'Help',
                body: '<p>Help content not found.</p>'
            };
        }
    };

    // ========================================
    // Initialization
    // ========================================

    function init() {
        // Initialize step navigation if steps exist
        if (document.querySelector('.step-card')) {
            StepNavigator.init();
        }

        // Add download button handlers
        document.querySelectorAll('[data-download]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const format = this.getAttribute('data-download') || 'pem';
                CertDownloader.download(format);
            });
        });

        // Add help button handlers
        document.querySelectorAll('[data-help]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const topic = this.getAttribute('data-help');
                HelpSystem.showHelp(topic);
            });
        });

        // Add copy button handlers
        document.querySelectorAll('[data-copy]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const text = this.getAttribute('data-copy');
                UI.copyToClipboard(text);
            });
        });

        // Log device info for debugging (remove in production)
        console.log('Device Info:', DeviceDetector.getDeviceInfo());
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose to global scope for inline handlers
    window.CertInstaller = {
        DeviceDetector: DeviceDetector,
        DownloadTracker: DownloadTracker,
        UI: UI,
        StepNavigator: StepNavigator,
        CertDownloader: CertDownloader,
        HelpSystem: HelpSystem
    };

})();

// Add CSS animations
(function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(20px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        @keyframes fadeOut {
            from { opacity: 1; transform: translateX(-50%) translateY(0); }
            to { opacity: 0; transform: translateX(-50%) translateY(20px); }
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .step-card.active {
            border-color: var(--primary-color, #3b82f6);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .step-card.completed {
            opacity: 0.7;
        }
        .step-card.completed::after {
            content: '\\2713';
            position: absolute;
            top: 12px;
            right: 12px;
            color: #10b981;
            font-size: 24px;
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);
})();
